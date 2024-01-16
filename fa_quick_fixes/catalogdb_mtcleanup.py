#!/usr/bin/env python
# -*- coding: utf-8 -*-

import oci 
import sys
import json 
from datetime import datetime, timedelta
import optparse
import time

def remove(oss_object_name,oss_bucket,oss_namespace):
    try:
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer, timeout=600)
        resp = object_storage.delete_object(oss_namespace, oss_bucket, oss_object_name)
        if resp.status == 204:
            return True
        else:
            return False
    except Exception as e:
        message="object deletion failed for obj {0} {1}".format(oss_object_name,e)
        print(message)

def parse_list_object(objects,oss_bucket,oss_namespace):
    try:
        for obj in objects.objects:
                    jdata=json.loads(str(obj))
                    obj_date=jdata["time_created"].split("T")[0]
                    oss_object_name=jdata["name"]
                    obj_del_elg=check_del_eligiblity(obj_date,oss_object_name)
                    if obj_del_elg:
                        oss_object_name=jdata["name"]
                        time.sleep(2)
                        # print(oss_object_name)
                        status=remove(oss_object_name,oss_bucket,oss_namespace)
                        if status:
                            print("{0} deleted successfully".format(oss_object_name))
        return objects.next_start_with
    except Exception as e:
        message="parse_list_object failed for obj {0} {1}".format(objects,e)
        print(message)

def check_del_eligiblity(obj_date,oss_object_name):
    try:
        obj_date=datetime.strptime(obj_date,'%Y-%m-%d')
        del_eligible = datetime.now() - timedelta(days=90)
        if "json" in oss_object_name or "log" in oss_object_name:
            ext=oss_object_name.split(".")[-1]
        if obj_date < del_eligible and ext in ["log","json"]:
            return True
        else:
            return False
    except Exception as e:
        message="delete eligiblity failed {0}".format(e)
        print(message)


def list_objects(oss_bucket, obj_name_prefix=None, oss_namespace=None):
        """ List objects in the bucket
        Args:
            oss_namespace (str): object namespace
            oss_bucket (str): object bucket
        Returns:
            objects (list): list of objects
        Raises:
            Exception: list_objects error
        """
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage = oci.object_storage.ObjectStorageClient(
                config={}, signer=signer, timeout=600)

            if obj_name_prefix:
                objects = object_storage.list_objects(oss_namespace, oss_bucket,prefix=obj_name_prefix,
                                                        fields="name,timeCreated").data
            else:
                objects = object_storage.list_objects(
                    oss_namespace, oss_bucket, fields="name,timeCreated").data

            next_start=parse_list_object(objects,oss_bucket,oss_namespace)
            count=0
            while  next_start :
                # print(next_start)
                
                if obj_name_prefix:
                    objects = object_storage.list_objects(oss_namespace, oss_bucket,prefix=obj_name_prefix,start=next_start,
                                                        fields="name,timeCreated").data
                else:
                    objects = object_storage.list_objects(
                        oss_namespace, oss_bucket, start=next_start,fields="name,timeCreated").data
                
                next_start=parse_list_object(objects,oss_bucket,oss_namespace)
                count=len(objects.objects) + count
                print(count)

        except Exception as e:
            message = "Failed to list objects!\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            print(message)




usage_str="pass the bucket name for which cleanup needs to be done"
def parse_opts():
    try:
        """ Parse program options """
        parser = optparse.OptionParser(usage=usage_str, version="%prog 1.0")
        parser.add_option('--ret_days', action='store', dest='ret_days',default="90", help='Used to specify ret days for objects')
        parser.add_option('--ns', action='store', dest='name_space',default="p1-saasfapreprod1", help='Used to specify name space for bucket')
        parser.add_option('--bucket-name', action='store', dest='bucket_name')
      
        (opts, args) = parser.parse_args()
        if not opts.bucket_name or not opts.ret_days:
            parser.error(
                '--bucket-name is require')
        return (opts, args)

    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[
                                                                 1:2])
        print(message)


def main():
    try:
        (options, args) = parse_opts()
        file_path  = options.ret_days
        bucket_name  = options.bucket_name
        name_space=options.name_space
        if bucket_name:
            list_objects(bucket_name,"",name_space)
    except Exception as e:
        message = "Failed to upload file!\n{0} {1}".format(sys.exc_info()[
                                                                 1:2],e)
        print(message)

if __name__ == "__main__":
    main()