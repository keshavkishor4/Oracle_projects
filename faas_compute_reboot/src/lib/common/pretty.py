# from prettytable import PrettyTable
from prettytable import PrettyTable
import string
import json

class ConsoleColor:
    # Color
    BLACK = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[97m'

    # Style
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    # BackgroundColor
    BgBLACK = '\033[40m'
    BgRED = '\033[41m'
    BgGREEN = '\033[42m'
    BgORANGE = '\033[43m'
    BgBLUE = '\033[44m'
    BgPURPLE = '\033[45m'
    BgCYAN = '\033[46m'
    BgGRAY = '\033[47m'

    # End
    END = '\033[0m'

def print_valid_info_pretty_table (var_file_name):
    try :
        # FILE_NAME="../../output/incident_TEST123_valid_pod_vms_for_reboot_list.json"
        with open(var_file_name,'r') as f:
            data = json.load(f)
            # print(data)

        x = PrettyTable()

        x.field_names = [ConsoleColor.BOLD + "data_center" + ConsoleColor.END, 
                         ConsoleColor.BOLD + "pod_name" + ConsoleColor.END, 
                         ConsoleColor.BOLD + "host_name" + ConsoleColor.END, 
                        #  ConsoleColor.BOLD + "vm_type" + ConsoleColor.END,
                         ConsoleColor.BOLD + "host_state" + ConsoleColor.END
                        #  ,
                        #  ConsoleColor.BOLD + "submit_time" + ConsoleColor.END
                        ]

        for fields in data:
            field_list = []
            field_list.append(fields["data_center"])
            field_list.append(fields["pod_name"])
            field_list.append(fields["host_name"])
            # field_list.append(fields["vm_type"])
            field_list.append(ConsoleColor.GREEN + fields["host_state"] + ConsoleColor.END)
            # field_list.append(fields["submit_time"])
            # print(field_list)
            x.add_row(field_list)

        print(x)
    except Exception as e:
        message = "Exception in pretty, Error while displaying the VALID info {0}".format(e)
        print("{0}".format(message))

def print_invalid_info_pretty_table (var_file_name):
    try :
        # FILE_NAME="../../output/incident_TEST123_valid_pod_vms_for_reboot_list.json"
        with open(var_file_name,'r') as f:
            data = json.load(f)
            # print(data)

        x = PrettyTable()

        x.field_names = [ConsoleColor.BOLD + "data_center" + ConsoleColor.END, 
                         ConsoleColor.BOLD + "pod_name" + ConsoleColor.END, 
                         ConsoleColor.BOLD + "host_name" + ConsoleColor.END, 
                         ConsoleColor.BOLD + "reason" + ConsoleColor.END
                        ]
        # ,
        #                  ConsoleColor.BOLD + "submit_time" + ConsoleColor.END]

        for fields in data:
            field_list = []
            field_list.append(fields["data_center"])
            field_list.append(fields["pod_name"])
            field_list.append(fields["host_name"])
            field_list.append(ConsoleColor.RED + fields["reason"] + ConsoleColor.END)
            # field_list.append(fields["submit_time"])
            # print(field_list)
            x.add_row(field_list)

        print(x)
    except Exception as e:
        message = "Exception in pretty, Error while displaying the INVALID info {0}".format(e)
        print("{0}".format(message))