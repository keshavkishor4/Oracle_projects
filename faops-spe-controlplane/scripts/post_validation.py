import os
import subprocess
from subprocess import call
import requests
import re
import sys
import time


def postvalexternal():
    global exit_status
    global workspace
    instance_type = sys.argv[1]
    # workspace = os.environ['WORKSPACE']
    # workspace = "/scratch/src/oci/kunal/tf_dev_networking/fasaasservicemgr/"
    os.chdir(workspace.rstrip() + "/provisioning/tfconfigs/ssm_instances")
    if instance_type == ('ssm_instance' or 'both'):
        ssm_external = subprocess.Popen("terraform output \"FA SSM Management LB Public IP Address\"",
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (ssmex_output, ssmex_err) = ssm_external.communicate()
        if ssmex_output != None:
            url = "http://" + ssmex_output.rstrip() + "/falcm-saasmgr/v2/pod-managers"
            print 'External URL : ', url
        else:
            print 'Error came : ', ssmex_err
            return
    retry_count = 0
    exit_status = 1
    while retry_count < 10 and exit_status != 0:
        time.sleep(20)
        retry_count += 1
        print "try_count", retry_count
        try:
            output_url = requests.get(url, verify=False, timeout=10)
            pattern = "\[\]"
            if re.search(pattern, output_url.text):
                print "Pass"
                exit_status = 0
            else:
                print "Fail"
                exit_status = 1
            time.sleep(10)
        except requests.exceptions.Timeout as errt:
            print ("Timeout Error:", errt)
            exit_status = 1
            time.sleep(10)

    if instance_type == ('lcm_instance' or 'both'):
        lcm_external = subprocess.Popen("terraform output \"FA LCM Management LB Public IP Address\"",
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (lcmex_output, lcmex_err) = lcm_external.communicate()
        if lcmex_output != None:
            url = "http://" + lcmex_output.rstrip() + "/falcm-podmgr/v2/pod-mgr/status"
            print 'External URL : ', url
        else:
            print 'Error came : ', lcmex_err
            return
        while retry_count < 10 and exit_status != 0:
            time.sleep(10)
            retry_count += 1
            print "retry_count", retry_count
            try:
                output_url = requests.get(url, verify=False, timeout=10)
                pattern = "magic"
                if re.search(pattern, output_url.text):
                    print "Pass"
                    exit_status = 0
                else:
                    print "Fail"
                    exit_status = 1
                time.sleep(10)
            except requests.exceptions.Timeout as errt:
                print ("Timeout Error:", errt)
                exit_status = 1
                time.sleep(10)


def postvalinternal():
    instance_type = sys.argv[1]
    global workspace
    Script_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(workspace.rstrip() + "/provisioning/tfconfigs/ssm_instances")
    if instance_type == ('ssm_instance' or 'both'):
        ssmin = subprocess.Popen("terraform output \"FA SSM Pod Managers\"", stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        (ssmin_output, ssmin_err) = ssmin.communicate()
        if ssmin_output != None:
            start = ' '
            end = ' ('
            s = ssmin_output
            ip = s[s.find(start) + len(start):s.rfind(end)]
            print ip
            url = "http://" + ip.rstrip() + ":8080/falcm-saasmgr/v2/pod-managers"
            print url
        else:
            print ssmin_err
            print "Ip is not available"
            return
        basion = subprocess.Popen("terraform output \"FA SSM Bastions\"", stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, shell=True)
        (output, err) = basion.communicate()
        start1 = ' '
        end1 = ' ('
        s1 = output
        Basionip = s1[s1.find(start1) + len(start1):s1.rfind(end1)]
        print "BAsion IP ", Basionip, "HostIP ", ip, "URL is ", url

        args = "sh " + Script_dir.rstrip() + "/login.sh" + " " + Basionip + " " + ip + " " + url + " " + workspace
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        Internal_output = output
        pattern = "\[\]"
        # out = c.text
        if re.search(pattern, Internal_output):
            print "Internal URL validation Passed for SSM"
        else:
            print " Internal URL validation Failed for SSM"
        sys.exit(1)

    if instance_type == ('lcm_instance' or 'both'):
        lcmin = subprocess.Popen("terraform output \"FA LCM Pod Managers\"", stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
        (lcmin_output, lcmin_err) = lcmin.communicate()
        if lcmin_output != None:
            start = ' '
            end = ' (rfu'
            s = lcmin_output
            ip = s[s.find(start) + len(start):s.rfind(end)]
            print ip
            url = "http://" + ip.rstrip() + ":8080/falcm-podmgr/v2/pod-mgr/status"
            print url
        else:
            print lcmin_err
            print "Ip is not available"
            return
        basion = subprocess.Popen("terraform output \"FA LCM Bastions\"", stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, shell=True)
        (output, err) = basion.communicate()
        start1 = ' '
        end1 = ' (rfu'
        s1 = output
        Basionip = s1[s1.find(start1) + len(start):s1.rfind(end1)]
        print "BAsion IP ", Basionip, "HostIP ", ip, "URL is ", url
        args = "sh " + Script_dir.rstrip() + "/login.sh" + " " + Basionip + " " + ip + " " + url + " " + workspace
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        Internal_output = output
        pattern = "\[\]"
        # out = c.text
        if re.search(pattern, Internal_output):
            print "Internal Validation Passed for Lcm"
        else:
            print "Internal Validation Failed for LCM"
        sys.exit(1)


workspace = sys.argv[2]
exit_status = 0
postvalinternal()
time.sleep(30)
postvalexternal()

if exit_status == 0:
    print "Tests Passed"
    sys.exit(0)
else:
    print "Test Failed"
    sys.exit(1)