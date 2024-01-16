import argparse;
import ConfigParser
import re;
import os;
import sys
from functools import partial
from itertools import chain

class Helper:
  def __init__(self, section, file):
    self.readline = partial(next, chain(("[{0}]\n".format(section),), file, ("",)))

def getTokens(line):
  tokens = []
  while (re.search(r"@(.+?)@", line.strip())):
    m = re.search(r"@(.+?)@", line.strip())
    tokens.append(m.group(1))
    line = re.sub(r"%s" % m.group(0), "", line)
  return tokens

def replaceTemplate(config, tmpl_dir, out_dir, fname):
  tmpl = tmpl_dir + "/" + fname
  trgt = out_dir + "/" + fname

  #If the file does not exist do nothing
  if not os.path.isfile(tmpl):
    print tmpl + " file doesnot exist, skipping"
    return
  else:
    print "Processing :" + tmpl

  tokens = fname.split("/")
  dpath = out_dir + "/" + "/".join(tokens[:-1])
  if os.path.isdir(dpath):
    print "%s already exists, delete it first"%dpath;
    exit(1)

  os.system("mkdir -p " + dpath)

  missing = []
  with open(tmpl) as tfh:
    lines = tfh.readlines()
    with open(trgt, "w") as tgfh:
      for line in lines:
        for token in getTokens(line):
          try:
            line = re.sub("@%s@" % token,config.get("Foo", token), line)
          except :
            missing.append(token)
        tgfh.write(line)
  if (len(missing) > 0 ) :
    print "WARNING: config.properties is missing parameters %s"%missing

parser = argparse.ArgumentParser(description='Create prod-plan.json and other files');
parser.add_argument('server', help='Specify if the server to be pushed is saasmgr, podmgr or podmgr-2')
parser.add_argument('cfg_dir', help='Config directory with config.properties')
parser.add_argument('tmpl_dir', help='Tenplate directory with sample files')
parser.add_argument('out_dir', help='Out Directory the merged files')
parser.add_argument('ovr_dir', help='Directory which contains override.properties file')
args = parser.parse_args()

config = ConfigParser.RawConfigParser(allow_no_value=False)
with open(args.cfg_dir + '/config.properties') as ifh:
  config.readfp(Helper("Foo", ifh))

config.set('Foo',"ociKeyFile", "/u01/oracle/configs/.oci/oci_api_key.pem")
config.set('Foo',"psmOciKeyFile", "/u01/oracle/configs/.psmoci/oci_api_key.pem")

#
# Load podmgr-2.properties and replace in config
#
if (args.server != 'saasmgr' and args.server != 'podmgr' ):
  podmgr =  ConfigParser.RawConfigParser(allow_no_value=False)
  with open(args.cfg_dir + "/%s.properties" % args.server) as ifh:
    podmgr.readfp(Helper("Foo", ifh))
  for (each_key, each_val) in podmgr.items("Foo"):
    print "Picking %s value %s from podmgr-2" % (each_key,each_val)
    config.set('Foo',each_key, each_val)

#
# Set the overrides here
#
try:
    ovr_cfg = ConfigParser.RawConfigParser(allow_no_value=False)
    with open(args.ovr_dir +"/override.properties") as ifh:
        ovr_cfg.readfp(Helper("Foo", ifh))
    for (each_key, each_val) in ovr_cfg.items("Foo"):
        print "Picking %s" % (each_key)
        config.set('Foo',each_key, each_val)
except:
    print "Cannot read " + args.ovr_dir +"/override.properties"

replaceTemplate(config, args.tmpl_dir, args.out_dir,'.falcm/cfg/prod-plan.json')
replaceTemplate(config, args.tmpl_dir, args.out_dir,'.oci/config')
replaceTemplate(config, args.tmpl_dir, args.out_dir,'.psmoci/config')
