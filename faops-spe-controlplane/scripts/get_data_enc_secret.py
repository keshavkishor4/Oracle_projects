#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#

from argparse import ArgumentParser
import oci
import re
import random
import string
import sys
from functools import partial
from itertools import chain
import ConfigParser
from Crypto.Cipher import AES
import base64
import time
import os
PADDING = '{'
BLOCK_SIZE = 32
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

class Helper(object):
    def __init__(self, section_name, file):
        self.file_iterator = chain(("[{}]\n".format(section_name),), file, ("",))

    def readline(self):
        return next(self.file_iterator)

#
# Fetch a random password
#
def gen_password(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(length))

#
# Encrypt the password with the given key
#
def enc_password(key, password):
    cipher = AES.new(base64.b64decode(key))
    return cipher.encrypt(pad(password))

#
# Decrypt the password with the given key
#
def dec_password(key, enc_str):
    cipher = AES.new(base64.b64decode(key))
    return cipher.decrypt(enc_str).rstrip(PADDING)

def get_args():
    parser = ArgumentParser()
    parser.add_argument("-r", "--region", required=True, help="Region Name")
    parser.add_argument("-c", "--config_dir", required=True, help="Path to config file Directory")
    parser.add_argument("-s", "--server", required=True, choices=["podmgr", "saasmgr"],
                        help="Server type: 'podmgr' or 'saasmgr'")

    return parser.parse_args()

def main():

    args = get_args()

    config = ConfigParser.RawConfigParser(allow_no_value=False)
    with open(os.path.join(args.config_dir, 'config.properties')) as ifh:
      config.readfp(Helper("Foo", ifh))

    config_dict = { "tenancy" : config.get("Foo", "ociTenancyId"),
                   "user" : config.get("Foo", "ociUserId"),
                   "fingerprint" : config.get("Foo", "ociFingerPrint"),
                   "key_file" : os.path.join(args.config_dir, ".oci", "oci_api_key.pem"),
                   "region" : args.region }

    identity = oci.identity.IdentityClient(config_dict)

    obj_storage = oci.object_storage.ObjectStorageClient(config_dict)
    namespace = obj_storage.get_namespace().data

    bucket = config.get("Foo", args.server + "DataEncKeyBucket")
    secret = config.get("Foo", args.server + "DataEncKeySecret")
    data_key = args.region + ".data_enc.key"
    password = ''
    data_key_exists = True

    #
    # Try getting the password from the Bucket
    #
    try:
        obj_data = obj_storage.get_object(namespace, bucket,
                                          data_key)
        password = obj_data.data.content
    except Exception as err:
        #
        # Check if the exception is due to missing data_key file
        #
        if (re.match(r"The object '%s' was not found"%(data_key), err.message)):
            data_key_exists = False
        else:
            print "Exception : " + str(err);
            sys.exit(-1)

    #
    # If the password does not exist in the bucket, create one random password and store it encrypted.
    #
    if  not data_key_exists :
        password = gen_password(10)
        enc_str = enc_password(secret, password)
        try:
            obj_storage.put_object(namespace, bucket,
                                   data_key, enc_str)
        except Exception as err:
            print "Exception : " + str(err)
            sys.exit(-1)
    else:
        #
        # Password exists, so decrypt it.
        #
        password = dec_password(secret,password)

    print base64.b64encode(password)

if __name__ == '__main__' :
    main()
