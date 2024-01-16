import time,oci,os,logging,sys,re
from argparse import ArgumentParser
from util import Util


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=True, help="make lots of noise [default]")
    parser.add_argument("-t", "--tenancy", required=True ,  help="tenancy name")
    parser.add_argument("-r", "--region" , required=True, help="region name")
    parser.add_argument("-e", "--env_type",  required=True, help="environment type : prod, test,staging, dev")
    parser.add_argument("-l", "--lcm_db_value", default="false", help="give true for lcm_db creation , false otherwise")
    parser.add_argument("-s", "--ssm_db_value", default="false", help="give true for ssm_db creation , false otherwise")
    parser.add_argument("-p", "--password", required=True, help= "password for db admin and fassm user for LCM and SSM management")
    parser.add_argument("-k", "--key_file", default="false" ,help="key file for the teancy and user")

    args = parser.parse_args()
    logger = ""
    utils = Util(logger)
    logger = utils.createlogger(sys.argv[0])
    util = Util(logger)

    # Values are hardcoded until we get terraform state file from ssm_network and lcm_network
    if args.tenancy == "saastestfa":
        config_dict = {'tenancy' : 'ocid1.tenancy.oc1..aaaaaaaavscbdfap4gdw4tjornkbwb67rgckzm6pimftu2alro6arqk364aa',
                       'user': 'ocid1.user.oc1..aaaaaaaaqxa3mxjct4bofmtf2o23oirfwvdvk3pt4f7b73nhb3krhzkchvla',
                       'fingerprint' : 'cb:50:21:c0:a9:0c:ed:52:d2:33:67:22:eb:dd:9c:39',
                       'key_file': '/root/.oci/oci_api_key.pem'}
    elif args.tenancy == "oraclefaonbm":
        config_dict = {'tenancy': 'ocid1.tenancy.oc1..aaaaaaaaf76usem7gyfrakr35anvky4tyowvdvbik7kbrcizlyjsgfxpdg2a',
                       'user': 'ocid1.user.oc1..aaaaaaaaiwrxusgfwf5wy3vwiu54z7bza5hsjmldtb5mk3d3nomthe36aoka',
                       'fingerprint': 'f3:66:3e:0e:bd:02:d2:f6:9c:5e:58:b2:7a:7f:27:08',
                       'key_file': '/scratch/src/oci/fig/.oci/oci_api_key.pem'}
    else :
        logger.error(" The config for this tenancy is not available. Exiting ....")
        sys.exit(1)

    if args.key_file != "false":
        config_dict.update({'key_file' : args.key_file})

    config_dict.update({'region' : args.region})
    config_dict.update({'env' : args.env_type})
    config_dict.update({'lcm_db_value' : args.lcm_db_value})
    config_dict.update({'ssm_db_value': args.ssm_db_value})
    config_dict.update({'private_key_password' : ''})

    if (re.search(r'\S*\w*[a-z]\w*\S*[a-z]\w*\S*', args.password) is not None) and \
        (re.search(r'\S*\w*[A-Z]\w*\S*[A-Z]\w*\S*', args.password) is not None) \
            and (re.search(r'\S*\w*[0-9]\w*\S*[0-9]\w*\S*', args.password) is not None) and (
        re.search(r'\S*\w*[\W,_]\w*\S*[\W,_]\w*\S*', args.password) is not None):
        config_dict.update({'password': args.password})
    else:
        logger.error(" Password strength check failed. Exiting ...")
        sys.exit(1)

    # Values are hardcoded until we get terraform state file from ssm_network and lcm_network
    if args.tenancy == "oraclefaonbm" and args.env_type == "test" and args.region == "us-phoenix-1":
        config_dict.update({'ssm_bastion_subnet_ids': '["ocid1.subnet.oc1.phx.aaaaaaaaqsxuxmzfeypejjprmzx2ws55r4cd7ulncpnh4jpwpucp7eprvama", "ocid1.subnet.oc1.phx.aaaaaaaaeqcly3kuqaopycblrutvxrf3nb3e36g5zqdixb54hrsfiye4ynxa", "ocid1.subnet.oc1.phx.aaaaaaaayzn3xmpzvkmehfw2fpbiac7chbypbsaq2cudoil2ysdug7ocptda"]'})
        config_dict.update({'ssm_lb_subnet_ids': '["ocid1.subnet.oc1.phx.aaaaaaaaipvm2xyso25tcyczkcdd3ihepewzu7cpt5jfa3yzf4np2tk7acfq", "ocid1.subnet.oc1.phx.aaaaaaaaikrkdjlvlu5gez3amhe2vu7qlkt5ujmla3he7qt7ev3strcjtmaa", "ocid1.subnet.oc1.phx.aaaaaaaa5dbt4fowmyfjpqdpzf5wdkld6ts5r34gzsvrn5ulfkd5dciyg5ea"]'})
        config_dict.update({'ssm_nat_subnet_ids': '["ocid1.subnet.oc1.phx.aaaaaaaatkrvk2k4pmswdmltg22uy5ro7ygilihlqebnhemelutvx6crkmhq", "ocid1.subnet.oc1.phx.aaaaaaaahp47btwififvjg23npgfru5i5gwfext3d3k5tl4lwmdallwwinqq", "ocid1.subnet.oc1.phx.aaaaaaaa2uykjbjuyswix4myrdl6hfmheqm62wp3h36456itbcy7dcuwinmq"]'})
        config_dict.update({'ssm_app_subnet_ids': '["ocid1.subnet.oc1.phx.aaaaaaaacvh225lgattpwg32ao65nluvcuoeorotgmgyhisjyumxxk2nn47q", "ocid1.subnet.oc1.phx.aaaaaaaajkviyolgqgvubd62ugmfexdfpuiju5jggltjsjempnmoe35pnwcq", "ocid1.subnet.oc1.phx.aaaaaaaazqaiffs3gssmprqezgiiwd3m4jrfyztae2m6t4yciz2zkhraghia"]'})
        config_dict.update({'ssm_database_subnet_ids': '["ocid1.subnet.oc1.phx.aaaaaaaanb5mssskyrwetjw6sykps57v3s27eq27y7ktxjmsoarddhmvziza", "ocid1.subnet.oc1.phx.aaaaaaaafvwmixwbhblv7w6263ozsxlyiyijq4faefgylcxvw2slcbkhik5a", "ocid1.subnet.oc1.phx.aaaaaaaar3oogzc4urrxe3iddh6lmqfjq3eear7v6lbtv7ohhdanqwgaqmcq"]'})
        config_dict.update({'pod_cidr_ranges': '["10.1.64.0/18", "10.1.128.0/17", "10.2.64.0/18", "10.2.128.0/17", "10.3.64.0/18", "10.3.128.0/17", "10.4.64.0/18", "10.4.128.0/17", "10.5.64.0/18", "10.5.128.0/17", "10.6.64.0/18", "10.6.128.0/17", "10.7.64.0/18", "10.7.128.0/17", "10.8.64.0/18", "10.8.128.0/17", "10.9.64.0/18", "10.9.128.0/17", "10.10.64.0/18", "10.10.128.0/17"]'})
        config_dict.update({'ssh_public_key_path': '../../../modules/common/src/test/resources/ssh/id_rsa.pub'})
        config_dict.update({'ssh_private_key_path': '../../../modules/common/src/test/resources/ssh/id_rsa'})
        config_dict.update({'psm_service_name': 'PSMTest'})
        config_dict.update({'ssm_vcn_cidr': '10.10.0.0/16'})
        config_dict.update({'lcm_vcn_cidr': '10.10.0.0/16'})
        config_dict.update({'pod_subnet_cap_for_dev_use': '6'})
    else:
        logger.error("Subnet is not available for selected tenancy , region and environment type")
        sys.exit(1)
    util.create_tf_vars_file(config_dict)