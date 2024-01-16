#!/bin/bash/python3.8
# -*- coding: utf-8 -*-
"""
    NAME
      backup_status.py
    DESCRIPTION
      implement backup monitoring methods
    NOTES

    MODIFIED        (MM/DD/YY)

    Vipin Azad       09/15/22 - initial version 
"""
from logging import exception
import requests
import json
import csv
from collections import defaultdict
import glob
import os
import time
# from dec import *
import urllib3
import smtplib
import os
import glob
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders, message
from datetime import datetime
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

regions = ["us-ashburn-1", "ap-tokyo-1", "eu-frankfurt-1", "me-jeddah-1", "ap-sydney-1", "ca-toronto-1", "eu-amsterdam-1", "ap-melbourne-1", "ap-osaka-1", "ca-montreal-1",
           "us-phoenix-1", "ap-mumbai-1", "eura.eu-frankfurt-1", "eu-zurich-1", "sa-saopaulo-1", "uk-london-1", "uk-gov-london-1", "me-dubai-1", "uk-cardiff-1", "ap-hyderabad-1", "sa-santiago-1", "ap-singapore-1"]
# regions = ["ap-sydney-1","ap-singapore-1" ]

#Tier1 Account details in dict format 
tier1 = {'us2dz2v': 'EEHO', 'us2gl1ec': 'EINO', 'us6ai5lc': 'EKDI',
         'ubpe55p': 'ENGE', 'us2fh9v': 'HDBZ', 'em3bk4iv': 'EGVH', 'ap1bizv': 'HDEK'}

out_dir = "/scratch/faopscb/faops_tasks/monitoring/faops_backup_monitoring/FAOPS_BACKUP_STATUS_OUT"
current_time = time.time()
td = datetime.now()

# Email Parameters
email_add = "vipin.azad@oracle.com;keshav.k.kishor@oracle.com;zakki.ahmed@oracle.com"
subject = "FA Backup Status"


def csv_gen(db_stat):
    now = datetime.now()
    date_time = now.strftime("%m%d%Y-%H%M%S")
    print("Generating CSV......")
    file = "{0}/{1}_{2}.csv".format(out_dir, "FAOPS_BACKUP_STATUS",
                                    date_time)
    data_file = open(file, 'w')
    header = ['Region', 'status', 'POD', 'Hostname', 'SID',
              'Backup_type', 'Db_role', 'RPM_VER', 'FAB_ERROR', 'Log_file', 'error']
    csv_writer = csv.DictWriter(data_file, fieldnames=header)
    csv_writer.writeheader()
    csv_writer.writerows(db_stat)
    data_file.close()


def db_stat():
    db_stat = []
    for reg in regions:
        if reg == "eura.eu-frankfurt-1":
            URL = "https://catalogdb-{0}.falcm.ocs.oraclecloud.com/ords/ocibakrev/backup/details".format(
                reg)
        else:
            URL = "https://catalogdb.{0}.falcm.ocs.oraclecloud.com/ords/ocibakrev/backup/details".format(
                reg)
        print(URL)

        headers = {'Accept': 'application/json'}
        retry_strategy = Retry(total=5, backoff_factor=1,
                               status_forcelist=[502, 503, 504, 500, 429])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.session()
        http.mount('https://', adapter)
        http.mount('http://', adapter)
        try:
            DATA = http.get(URL, headers=headers, verify=False, timeout=600)
            if DATA.status_code != 500:
                backup_metadata = json.loads(DATA.text)

                for sts in backup_metadata:
                    dict1 = {}
                    SID = sts['CLIENT_NAME']
                    Hostname = sts['HOSTNAME']
                    status = sts['STATUS']
                    backuptype = sts['BACKUP_TYPE']
                    dbrole = sts['DB_ROLE']
                    RPMVER = sts['RPM_VER']
                    log_name = sts['LOG_FILE'].split("/")
                    log_file_name = log_name[-1]

                    if SID in tier1:

                        dict1['Region'] = reg
                        dict1['status'] = status
                        dict1['POD'] = tier1[SID]
                        dict1['Hostname'] = Hostname
                        dict1['SID'] = SID
                        dict1['Backup_type'] = backuptype
                        dict1['Db_role'] = dbrole
                        dict1['RPM_VER'] = RPMVER
                        if reg == "eura.eu-frankfurt-1":
                            log_url = "https://catalogdb-{0}.falcm.ocs.oraclecloud.com/ords/ocibakrev/getlog?file={1}".format(
                                reg, log_file_name)
                        else:
                            log_url = "https://catalogdb.{0}.falcm.ocs.oraclecloud.com/ords/ocibakrev/getlog?file={1}".format(
                                reg, log_file_name)
                        print(log_url)
                        dict1['Log_file'] = '=HYPERLINK("{0}")'.format(log_url)
                        log_data = http.get(
                            log_url, headers=headers, verify=False, timeout=600)
                        log_data_file = log_data.text.split('\n')
                        rep = []
                        error = ''
                        for dt in log_data_file:
                            if "KBHS-01404" in dt or "Error" in dt or "Failed" in dt or "ERROR MESSAGE STACK FOLLOWS" in dt or "RMAN-03002" in dt or "RMAN-06012" in dt or "ORA-" in dt or "RMAN-03009" in dt or "RMAN-10038" in dt or "failed" in dt:
                                if dt in rep:
                                    pass
                                else:
                                    error = error + dt
                                rep.append(dt)
                        rep.clear()
                        if "wallet is not open" in error:
                            dict1['FAB_ERROR'] = "FAB_002"
                        elif "commonutils.check_conflicts" in error:
                            dict1['FAB_ERROR'] = "FAB_001"
                        elif "master key not yet set" in error or "RMAN does not support PKI-based master key for encryption" in error:
                            dict1['FAB_ERROR'] = "FAB_003"
                        elif "ORA-01089: immediate shutdown" in error or "ORA-01092: ORACLE instance terminated" in error:
                            dict1['FAB_ERROR'] = "FAB_004"
                        elif "ORA-16456: switchover to standby in progress" in error:
                            dict1['FAB_ERROR'] = "FAB_005"
                        elif "Connection reset by peer" in error:
                            dict1['FAB_ERROR'] = "FAB_006"
                        elif "RMAN-10038" in error:
                            dict1['FAB_ERROR'] = "FAB_007"
                        elif "ORA-19506: failed to create sequential file" in error:
                            dict1['FAB_ERROR'] = "FAB_008"
                        elif "Failed to do verify oss destination" in error:
                            dict1['FAB_ERROR'] = "FAB_009"
                        elif "FUSION_PDB value is null" in error:
                            dict1['FAB_ERROR'] = "FAB_010"
                        dict1['error'] = error.replace(',', '')
                        if status == 'SUCCESS' and "KBHS-01404" in error:
                            db_stat.append(dict1)
                        elif status == "FAILED":
                            db_stat.append(dict1)

                    elif status == 'FAILED' and SID:
                        dict1['Region'] = reg
                        dict1['status'] = status
                        dict1['Hostname'] = Hostname
                        dict1['SID'] = SID
                        dict1['Backup_type'] = backuptype
                        dict1['Db_role'] = dbrole
                        dict1['RPM_VER'] = RPMVER
                        if reg == "eura.eu-frankfurt-1":
                            log_url = "https://catalogdb-{0}.falcm.ocs.oraclecloud.com/ords/ocibakrev/getlog?file={1}".format(
                                reg, log_file_name)
                        else:
                            log_url = "https://catalogdb.{0}.falcm.ocs.oraclecloud.com/ords/ocibakrev/getlog?file={1}".format(
                                reg, log_file_name)
                        print(log_url)
                        dict1['Log_file'] = '=HYPERLINK("{0}")'.format(log_url)
                        log_data = http.get(
                            log_url, headers=headers, verify=False, timeout=600)
                        log_data_file = log_data.text.split('\n')
                        rep = []
                        error = ''
                        for dt in log_data_file:
                            if "Error" in dt or "Failed" in dt or "ERROR MESSAGE STACK FOLLOWS" in dt or "RMAN-03002" in dt or "RMAN-06012" in dt or "ORA-" in dt or "RMAN-03009" in dt or "RMAN-10038" in dt or "failed" in dt:
                                if dt in rep:
                                    pass
                                else:
                                    error = error + dt
                                rep.append(dt)
                        rep.clear()

                        if "wallet is not open" in error:
                            dict1['FAB_ERROR'] = "FAB_002"
                        elif "commonutils.check_conflicts" in error:
                            dict1['FAB_ERROR'] = "FAB_001"
                        elif "master key not yet set" in error or "RMAN does not support PKI-based master key for encryption" in error:
                            dict1['FAB_ERROR'] = "FAB_003"
                        elif "ORA-01089: immediate shutdown" in error or "ORA-01092: ORACLE instance terminated" in error:
                            dict1['FAB_ERROR'] = "FAB_004"
                        elif "ORA-16456: switchover to standby in progress" in error:
                            dict1['FAB_ERROR'] = "FAB_005"
                        elif "Connection reset by peer" in error:
                            dict1['FAB_ERROR'] = "FAB_006"
                        elif "RMAN-10038" in error:
                            dict1['FAB_ERROR'] = "FAB_007"
                        elif "ORA-19506: failed to create sequential file" in error:
                            dict1['FAB_ERROR'] = "FAB_008"
                        elif "Failed to do verify oss destination" in error:
                            dict1['FAB_ERROR'] = "FAB_009"
                        elif "FUSION_PDB value is null" in error:
                            dict1['FAB_ERROR'] = "FAB_010"
                        dict1['error'] = error.replace(',', '')
                        db_stat.append(dict1)

        except Exception as e:
            print(e)
    db_stat1 = []
    for x in db_stat:
        if x not in db_stat1:
            db_stat1.append(x)
    csv_gen(db_stat1)


def csv_purge():
    print(out_dir)
    post_file_list = glob.glob(
        "{0}/FAOPS_BACKUP_STATUS*.csv".format(out_dir))
    for f in post_file_list:
        creation_time = os.path.getctime(f)
        # purging files older than 30 days
        if (current_time - creation_time) // (24 * 3600) >= 10:
            os.unlink(f)
            print('{} removed'.format(f))


def send_email_fct(filename=None, filepath=None, toaddr=None, subject=None, body=None):

    from_email_addr = "vipin.azad@oracle.com"
    msg = MIMEMultipart('alternative')
    msg['From'] = from_email_addr
    msg['To'] = toaddr
    msg['Subject'] = subject

    text = "Hi!\nPlease find the below status details for Tier1 customers : \n"

    html = body
    # print(html)
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    # with file attachments
    # msg.attach(MIMEText(body_email, 'plain'))

    attachment = open(filepath, 'rb')  # open the file to be sent

    p = MIMEBase('application', 'octet-stream')  # instance of MIMEBase
    p.set_payload(attachment.read())
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    # msg.attach(p)  # attach the instance 'p' to instance 'msg'

    s = smtplib.SMTP('localhost')  # SMTP
    s.ehlo()
    s.starttls()
    #s.login(from_email_addr, passwd)
    #
    if subject == None:
        subject = "Test"
    if body == None:
        body = "this is the body"
    if toaddr == None:
        toaddr = "vipin.azad@oracle.com"

    s.sendmail(from_email_addr, toaddr.split(';'), msg.as_string())
    # s.sendmail(from_email_addr, toaddr, message.encode('ascii', 'ignore').decode('ascii'))  # sending the email

    s.quit()  # terminating the session


def csv_parser():

    post_file_list = glob.glob(
        "{0}/FAOPS_BACKUP_STATUS*.csv".format(out_dir))
    print(post_file_list)
    latest_file = max(post_file_list, key=os.path.getctime)
    print(latest_file)
    filein = open(latest_file, "r")
    # fileout = open("html-table.html", "w")
    data = filein.readlines()

    table = "<html>\n<head></head>\n<body>\n<h1>Backup Status on {0}</h1>\n<table>\n".format(
        td)

    # Create the table's column headers
    header = data[0].split(",")
    table += "  <tr>\n"
    for column in header:
        table += "    <th {1}>{0}</th>\n".format(
            column.strip(), "style=\"background-color:#ccd180\"")
    table += "  </tr>\n"

    # Create the table's row data
    for line in data[1:]:
        row = line.split(",")
        if "EEHO" in row or "EINO" in row or "HDEK" in row or "EKDI" in row or "ENGE" in row or "HDBZ" in row or "EGVH" in row:
            table += "  <tr>\n"
            if "FAILED" in row:
                for column in row:
                    if "catalogdb" in column:
                        table += "    <td {1}><a href=\"{0}\"><div style=\"height:100%;width:100\%\">logfile</div></td>\n".format(
                            column.strip().replace('=HYPERLINK(', '').replace(')', '').replace('"', ''), "style=\"background-color:#FFCCCB\"", "")
                    else:
                        table += "    <td {1}>{0}</td>\n".format(
                            column.strip(), "style=\"background-color:#FFCCCB\"")

                table += "  </tr>\n"

            else:
                for column in row:
                    if "catalogdb" in column:
                        table += "    <td {1}><a href=\"{0}\"><div style=\"height:100%;width:100\%\">logfile</div></td>\n".format(
                            column.strip().replace('=HYPERLINK(', '').replace(')', '').replace('"', ''), "style=\"background-color:#D3D3D3\"", "")
                    else:
                        table += "    <td {1}>{0}</td>\n".format(
                            column.strip(), "style=\"background-color:#D3D3D3\"")
                table += "  </tr>\n"

    table += "</table>\n</html>"
    print(table)
    print(latest_file)
    file = latest_file.split('/')[-1].strip()
    send_email_fct(filename=file, filepath=latest_file,
                   toaddr=email_add, subject=subject, body=table)
    # fileout.writelines(table)
    # fileout.close()
    filein.close()
    # with open("html-table.html", r) as f:
    #     body = f.read
    #     print(body)
    #send_email_fct(filename=None, filepath=None, toaddr=None, subject=None, body=None)


def main():
    db_stat()
    csv_purge()
    csv_parser()


if __name__ == "__main__":
    main()
