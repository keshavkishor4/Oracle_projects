#!/usr/bin/python
import time,oci,os,logging,subprocess,json,sys
from argparse import ArgumentParser
from configparser import ConfigParser

class Util:

    def __init__(self,logger,**kwargs):
        self.logger = logger

    def create_tf_vars_file(self,config):
        self.config = config
        self.logger.info("Creating env vars file ")
        region_key_dict = {'us-phoenix-1' : 'phx', 'eu-frankfurt-1': 'fra', 'us-ashburn-1' : 'iad'}
        if self.config["env"].lower() == "dev":
            is_dev = "true"
        else:
            is_dev = "false"

        ssm_app_compartment_id = self.get_compartment_ocid(self.config["env"].upper()+'_FASSM')
        ssm_db_compartment_id = self.get_compartment_ocid(self.config["env"].upper()+'_FASSM_DATABASE')
        lcm_podm_compartment_id = self.get_compartment_ocid(self.config["env"].upper()+'_FALCM_POD_MGMT')
        lcm_db_compartment_id = self.get_compartment_ocid(self.config["env"].upper()+'_FALCM_DATABASE')
        local_work_dir = "/tmp"

        key_list = {
            'tenancy_ocid' : self.config["tenancy"] , 'user_ocid' : self.config["user"] ,'fingerprint' : self.config["fingerprint"],
            'private_key_path' : self.config["key_file"] ,'region' : self.config["region"] , 'region_key' : region_key_dict.get(self.config["region"]),
            'env' : self.config["env"], 'ssm_management_db_admin_password' : self.config["password"], 'local_work_dir' : local_work_dir,
            'ssm_management_db_fassm_user_password' : self.config["password"], 'ssm_app_compartment_id' : ssm_app_compartment_id,
            'ssm_db_compartment_id' : ssm_db_compartment_id, 'lcm_management_db_admin_password' : self.config["password"],
            'lcm_management_db_fassm_user_password' : self.config["password"], 'lcm_podm_compartment_id' : lcm_podm_compartment_id ,
            'lcm_db_compartment_id' : lcm_db_compartment_id, 'ssh_public_key_path' : self.config["ssh_public_key_path"],
            'ssh_private_key_path' : self.config["ssh_private_key_path"], 'psm_service_name' : self.config["psm_service_name"],
            'ssm_vcn_cidr' : self.config["ssm_vcn_cidr"], 'lcm_vcn_cidr' : self.config["lcm_vcn_cidr"], 'private_key_password' : self.config["private_key_password"]
        }

        key_list1 = {
            'is_dev' : is_dev, 'create_ssm_management_db' : self.config["ssm_db_value"], 'create_lcm_management_db' : self.config["lcm_db_value"] ,
            'ssm_bastion_subnet_ids' : self.config["ssm_bastion_subnet_ids"], 'ssm_lb_subnet_ids' : self.config["ssm_lb_subnet_ids"],
            'ssm_nat_subnet_ids' : self.config["ssm_nat_subnet_ids"], 'ssm_app_subnet_ids' : self.config["ssm_app_subnet_ids"],
            'ssm_database_subnet_ids' : self.config["ssm_database_subnet_ids"], 'pod_cidr_ranges' : self.config["pod_cidr_ranges"],
            'pod_subnet_cap_for_dev_use' : self.config["pod_subnet_cap_for_dev_use"]
        }

        build_no = os.environ["BUILD_ID"]
        workspace = os.environ["WORKSPACE"]
        with open(workspace+"/terraform_"+build_no+".tfvars", "w") as tfvars:
            for key, value in key_list.iteritems():
                print key + "=" + str(value)
                tfvars.write(key + '=' + '"'+str(value)+'"' + '\n')
            for key, value in key_list1.iteritems():
                print key + "=" + str(value)
                tfvars.write(key + '=' + str(value)  + '\n')

    def create_image(self):
        config = self.config
        computeclient = oci.core.ComputeClient(config)
        image_details = oci.core.models.CreateImageDetails(compartment_id=config["compartment"],
                                                           instance_id=config["instance"],
                                                           display_name=config["display_name"])
        image_resp= computeclient.create_image(image_details).data
        status = 0
        if (image_resp.lifecycle_state != "PROVISIONING"):
            print "Request for Custom Image Creation fails \n"+str(image_resp)
            status =1
            return status
        print "Request for Custom Image Creation is successfully submitted"
        image_list = computeclient.list_images(config["compartment"], display_name=config["display_name"]).data

        print "Current State : " + image_list[0].lifecycle_state
        retry_count = 6
        while (image_list[0].lifecycle_state != "AVAILABLE"):
            print "Waiting for Image State to be AVAILABLE"
            if retry_count == 0:
                print "Time out after 18 min \n"+str(image_list[0])
                status = 1
                return status
            time.sleep(180)  #sleeps for 3 min
            image_list = computeclient.list_images(config["compartment"], display_name=config["display_name"]).data
            print "Current State : " + image_list[0].lifecycle_state
            retry_count = retry_count -1

        print "Image is created successfully \n"+str(image_list[0])
        return status

    def get_compartment_ocid(self,compartment_name):
        config = self.config
        identity = oci.identity.IdentityClient(config)
        compartments = identity.list_compartments(config["tenancy"]).data
        for compartment in compartments:
            if compartment.name == compartment_name:
                return compartment.id

    def createlogger(self,name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    class ReturnException(Exception):
        def __init__(self, return_value):
            self.return_value = return_value

    def execute(self,cmd):
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                                 shell=True, bufsize=1)
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        for stderr_line in iter(popen.stderr.readline, ""):
            yield stderr_line
        popen.stdout.close()
        return_code = popen.wait()
        raise self.ReturnException(return_code)

    def run_command(self,command, logger=None, get_output=False):
        if get_output:
            if logger is None:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return process.stdout.read() + process.stderr.read()
            else:
                output = ""
                logger.info("------Executing command " + command + "------")
                try:
                    for line in self.execute(command):
                        logger.debug(line.decode('utf-8').rstrip())
                        output += line
                except self.ReturnException:
                    logger.info("------Finished command " + command + "-------")
                    return output
        else:
            if logger is None:
                return subprocess.call(command, shell=True)
            else:
                logger.info("------Executing command " + command + "------")
                try:
                    for line in self.execute(command):
                        logger.debug(line.decode('utf-8').rstrip())
                except self.ReturnException as e:
                    logger.info("------Finished command " + command + "-------")
                    return e.return_value

    # Read & parse json file
    def read_json_file(logger=None, file_name=None):
        data = json.loads(open(file_name, "r").read())
        return data

    def run_interactive_command(command, input_string, logger=None):
        if logger is None:
            p = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE, shell=True)
            p.stdin.write(input_string)
            p.communicate()
            return p.poll()
        else:
            logger.info("------Executing command " + command + "------")
            p = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE, shell=True)
            p.stdin.write(input_string)
            stdout, stderr = p.communicate()
            logger.debug(stdout + stderr)
            logger.info("------Finished command " + command + "-------")
            return p.poll()

    def config_from_file(self,file_location, profile_name):
        config = {}
        parser = ConfigParser(interpolation=None)
        if not parser.read(file_location):
            self.logger.error("Could not find config file at {}".format(file_location))
            sys.exit(1)
        if profile_name not in parser:
            self.logger.error("Profile '{}' not found in config file {}".format(profile_name, file_location))
            sys.exit(1)
        config.update(parser[profile_name])
        return config




