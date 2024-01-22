#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    NAME
      apscom.py

    DESCRIPTION
      Common module

    NOTES

    MODIFIED   (MM/DD/YY)
    Chenlu Chen 01/23/19 - Add Instance Principal support
    Chenlu Chen 09/26/18 - Port from self healing, written by jsoolee.
    Zakki Ahmed 09/22/22 - Added Enhancments
"""

from __future__ import absolute_import, division, print_function

__version__ = "20190123.1"

import os
import sys
import re
import time
from datetime import datetime, timedelta
import logging
from subprocess import Popen, PIPE
import signal
import pwd
import grp
from getpass import getuser
import traceback
from collections import OrderedDict
import json
import errno
import cmd

class colors:
    reset = '\033[0m'
    red = '\033[31m'
    green = '\033[32m'
    orange = '\033[33m'
    blue = '\033[34m'
    yellow = '\033[93m'

"""Global Variables
"""
com_prop = {}
msg_prop = {}
ALARM_TIMEOUT = 30
hostname = None
logger = None

"""runtime attributes"""
call_stack = False          # if True: print_stack()
silence_warn = False        # if True: silence warn(msg)

class AutoDict(dict):
    """Implementation of perl's autoVivification feature
    """
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value

"""Public Functions
"""
"""logging functions"""
def init_logger(main_script, log_dir=None,basename_wo_ext=None,logfile=None):
    """init logger, e.g. apscomm.init_logger(__file__)
    Args:
        main_script (str): main calling script
    Returns:
        str: logfile
    Raises:
        Exception: logging module error
    """
    try:
        global logger

        start_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        main_script = os.path.abspath(main_script)
        if not basename_wo_ext:
            basename_wo_ext = os.path.splitext(os.path.basename(main_script))[0]

        logger = logging.getLogger(main_script)
        if len(logger.handlers):
            handler = logger.handlers[0]
            logfile = handler.baseFilename
            return logfile

        if log_dir is None:
            log_dir = "/var/log/{0}".format(basename_wo_ext)
        else:
            log_dir = "{0}/{1}".format(log_dir, basename_wo_ext)

        log_dir = os.path.abspath(log_dir)
        if not os.path.isdir(log_dir):
            if not create_dir(log_dir):
                error("init_logger() failed!")

        logger.setLevel(logging.DEBUG)
        if not logfile:
            logfile = "{0}/{1}_{2}.log".format(log_dir, get_hostname()+"_"+ basename_wo_ext, start_time)
        handler = logging.FileHandler(logfile, "w")
        formatter = logging.Formatter("[%(asctime)s][%(levelname)-4s]%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        _pid = os.getpid()
        info("{0} logging started, PID {1}".format(logfile, _pid))
        return logfile

    except:
        error("{0}".format(sys.exc_info()[1:2]))


def debug(msg):
    """DEBUG message wrapper
    Args:
        msg (str): message.
    Returns:
        None
    """
    _log_msg("DEBUG", "[{0}] - {1}".format(sys._getframe(1).f_code.co_name, msg))

print_debug = debug

def info(msg):
    """INFO message wrapper
    Args:
        msg (str): message.
    Returns:
        None
    """
    _log_msg("INFO", "[{0}] - {1}".format(sys._getframe(1).f_code.co_name, msg))

print_info = info

def warn(msg):
    """WARN message wrapper
    Args:
        msg          (str): message.
    Returns:
        None
    """
    if not silence_warn:
        _log_msg("WARN", "[{0}] - {1}".format(sys._getframe(1).f_code.co_name, msg))

    if call_stack:
        print_stack()

print_warn = warn

def error(msg):
    """ERROR message wrapper
    Args:
        msg (str): message.
    Returns:
        None
    """
    _log_msg("ERROR", "[{0}] - {1}".format(sys._getframe(1).f_code.co_name, msg))
    if call_stack:
        print_stack()

    sys.exit(1)

print_error = error

def apsmsg(error_code, msg_format="D", status_type="FAILED"):
    """error code wrapper
    Args:
        error_code  (str): error code, e.g. "SH-4031-0001"
        msg_format  (str): (default="D") S or D, i.e. S for status, D for detailed description
        status_type (str): (default="FAILED") FAILED/SUCCESS/NOACTION/MANUAL
    Returns:
        None
    Raises:
        Exception: error_code data not found in json
    """
    msg_formats = ["S", "D"]
    status_types = ["FAILED", "SUCCESS", "NOACTION", "MANUAL"]

    try:
        if not msg_format in msg_formats:
            raise ValueError("'{0}' is not a supported msg_format! {1} are the supported msg_formats.".format(msg_format, msg_formats))

        if not status_type in status_types:
            raise ValueError("'{0}' is not a supported status_type! {1} are the supported status_types.".format(status_type, status_types))

        module_code = error_code[3:7]
        error_dict = msg_prop["ERROR_CODES"][module_code]["ERROR_LIST"].get(error_code, None)
        if error_dict is None:
            raise ValueError("Failed to find error code {0} from apsmsg.json!".format(error_code))

        if msg_format == "D":
            msg = "{0}: {1}\nCause:  {2}\nAction: {3}\nBucket: {4}".format(error_code, error_dict["DESCRIPTION"], error_dict["CAUSE"], error_dict["ACTION"], error_dict["BUCKET"])
        else:
            msg = "ADDL_INFO= {0}: {1}, STATUS:{2},RETRY:0".format(error_code, error_dict["DESCRIPTION"], status_type)

        _log_msg("WARN", "[{0}]\n{1}".format(sys._getframe(1).f_code.co_name, msg))

    except:
        msg = "Failed to run apsmsg!\n{0}".format(sys.exc_info()[1:2])
        warn(msg)
        raise


def raise_exc(error_code):
    """raise Exception wrapper
    Args:
        error_code  (str): error code, e.g. "SH-4031-0001"
    Returns:
        None
    Raises:
        Exception: raise Exception w/ error_code added
    """
    raise Exception(sys.exc_info()[1:2], error_code)


def get_exc_list():
    """get the list of error codes raised
    Args:
    Returns:
        list: list of error codes raised, e.g. ["SH-4031-0001", "SH-4031-0002"]
    """
    if sys.exc_info():
        return [x.group() for x in re.finditer('SH-\w{4}-\d{4}', str(sys.exc_info()[1]))]


def _apsmsg(msg_id, event=None, cause=None):
    """SRA-xxxx message wrapper
    Args:
        msg_id (str): msg id, e.g. "0001"
        event  (str): (default=None) CA event
        cause  (str): (default=None) cause message.
    Returns:
        None
    """
    try:
        msg_item = msg_prop.get(msg_id, None)
        if msg_item is None:
            warn("Failed to locate message of SRA-{}!".format(msg_id))
            return

        desc = msg_item["desc"]
        if event:
            desc = desc.replace("action", "action for {}".format(event), 1)

        if cause is None:
            msg = "SRA-{0}: {1}\nStatus: {2}\nAction: {3}".format(msg_id, desc, msg_item["status"], msg_item["action"])
        else:
            msg = "SRA-{0}: {1}\nStatus: {2}\nCause: {3}\nAction: {4}".format(msg_id, desc, msg_item["status"], cause, msg_item["action"])

        print(msg)
        debug(msg)
    except:
        msg = "Failed to run apsmsg!\n{0}".format(sys.exc_info()[1:2])
        warn(msg)
        raise


def msg_pass(msg, width=80):
    """info wrapper with "PASS" str
    Args:
        msg (str): message.
    Returns:
        None
    """
    info("{0:{1}s} - PASS".format(msg, width))


def msg_fail(msg, width=80):
    """info wrapper with "FAIL" str
    Args:
        msg (str): message.
    Returns:
        None
    """
    info("{0:{1}s} - FAIL".format(msg, width))


def msg_skip(msg, width=80):
    """info wrapper with "SKIP" str
    Args:
        msg (str): message.
    Returns:
        None
    """
    info("{0:{1}s} - SKIP".format(msg, width))


def print_stack():
    """print DEBUG call stack during ERROR
    Args:
    Returns:
        None
    """
    traceback.print_stack()


"""File handling functions"""
def check_file_owner(filename, owner="root"):
    """check file owner
    Args:
        filename (str): filename
        owner    (str): expected file owner
    Returns:
        bool: True if owner == file_owner
    """
    if not file_exists(filename):
        return False

    file_owner = pwd.getpwuid(os.stat(filename).st_uid).pw_name
    if file_owner == owner:
        return True
    else:
        return False


def create_dir(dirname):
    """create dir
    Args:
        dirname (str): dirname
    Returns:
        bool: True if succeeded, False if exists or failed
    """
    try:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            return True
        else:
            warn("Directory {0} exists already!".format(dirname))
            return False
    except IOError as e:
        warn("I/O error({0}): {1}".format(e.errno, e.strerror))
        return False
    except:
        warn(sys.exc_info()[1:2])
        return False


def file_empty(filename):
    """file empty?, size zero?
    Args:
        filename (str): filename
    Returns:
        bool: True if file size == 0
    """

    if os.stat(filename).st_size == 0:
        return True
    else:
        return False


def dir_exists(dirname):
    """dir exists?
    Args:
        dirname (str): dirname
    Returns:
        bool: True if dir
    """
    if os.path.isdir(dirname):
        return True
    else:
        warn("Directory %s doesn't exist!" % dirname)
        return False


def file_exists(filename):
    """file exists?
    Args:
        filename (str): filename
    Returns:
        bool: True if file exists
    """
    if os.path.isfile(filename):
        return True
    else:
        warn("File %s doesn't exist!" % filename)
        return False


def get_file_owner(filename):
    """get file owner
    Args:
        filename (str): filename
    Returns:
        tuple: (username, groupname)
    """
    return (pwd.getpwuid(os.stat(filename).st_uid).pw_name,
            grp.getgrgid(os.stat(filename).st_gid).gr_name)


"""run_cmds functions"""
class Alarm(Exception):
    """Alarm Exception"""
    pass

def _alarm_handler(signum, frame):
    """signal hanlder"""
    raise Alarm


def run_cmd(*cmds, **kwargs):
    """run cmd as root
    Args:
        *cmds
            cmd1        (list): cmd to run
            cmd2        (list): (optional) cmd piped; cmd1 | cmd2
        **kwargs
            envs         (ENV): ENV = os.environ.copy()
            abort       (bool): (default=False) if True, abort on errors. If False, warn on errors
            timeout     (bool): (default=True) to timeout when running longer than ALARM_TIMEOUT or timeout_secs
            timeout_secs (int): (default=30) timeout in sec
    Returns:
        str: cmd output, exit if erred and abort is True
    Raises:
        Exception:  invalid cmd/subprocess/timeout errors
    """
    _env = None
    abort = False
    timeout = True
    user = None
    _shell = False
    _shell_piped = False
    shell_true_cmds = ["cp"]

    try:
        # parse *cmds
        cnt = len(cmds)
        if cnt == 1:
            piping = False
        elif cnt == 2:
            piping = True
        else:
            raise ValueError("Invalid cmds: {0}".format(cmds))

        # parse **kwargs
        for key, value in kwargs.items():
            if key == "envs":
                _env = value
            elif key == "abort":
                abort = value
            elif key == "timeout":
                timeout = value
            elif key == "user":
                user = value

        if user:    # called from run_cmd_as_user
            uid, gid = get_uid(user)
            if uid is None:
                raise ValueError("Failed to get {0} uid!".format(user))

        if timeout:
            signal.signal(signal.SIGALRM, _alarm_handler)
            timeout_secs = kwargs.get("timeout_secs", None)
            if timeout_secs is None:
                timeout_secs = ALARM_TIMEOUT
            signal.alarm(timeout_secs)

        # cmd1 run
        if any(s == cmds[0][0] for s in shell_true_cmds):
            _shell = True       # shell=True is needed for /bin/cp "../crsd*.trc" <target_dir>
            cmd1 = ' '.join(cmds[0])
        else:
            cmd1 = cmds[0]

        if user:
            p1 = Popen(cmd1, stdout=PIPE, stderr=PIPE, preexec_fn=set_uid(uid, gid), shell=_shell, env=_env)
        else:
            p1 = Popen(cmd1, stdout=PIPE, stderr=PIPE, shell=_shell, env=_env)

        # cmd2 run
        if piping:
            if any(s == cmds[1][0] for s in shell_true_cmds):
                _shell_piped = True
                cmd2 = ' '.join(cmds[1])
            else:
                cmd2 = cmds[1]

            if user:
                p2 = Popen(cmd2, stdin=p1.stdout, stdout=PIPE, stderr=PIPE, preexec_fn=set_uid(uid, gid), shell=_shell_piped, env=_env)
            else:
                p2 = Popen(cmd2, stdin=p1.stdout, stdout=PIPE, stderr=PIPE, shell=_shell_piped, env=_env)

            out, err = p2.communicate()
            rc = int(p2.returncode)
        else:
            out, err = p1.communicate()
            rc = int(p1.returncode)

        """some cmd returns 1 even if completed successfully
            rc=1; i.e., catchall for general errors
            e.g. /etc/init.d/init.tfa start
        """
        out = out.strip()
        if rc == 0:
            return out
        elif rc == 1:
            # grep handling, e.g. cmd1 = ["ssh", "slcc31celadm01", "grep", "-c", "hugeee", "/etc/sysctl.conf"]
            cmd_list = []
            grep_cmd = ["grep", "egrep"]

            for cmd in cmds:
                cmd_list += cmd

            grep_found = any(i in grep_cmd for i in cmd_list)

            if "TFA Started and listening for commands" in out:
                return out
            else:
                if grep_found:
                    return out
                else:
                    raise ValueError("Failed to run cmd: {0} - returncode={1}!\n{2}".format(cmds, rc, out))
        else:
            raise ValueError("Failed to run cmd: {0} - returncode={1}!\n{2}\n{3}".format(cmds, rc, out, err))

    except ValueError as msg:
        raise ValueError(msg)
    except Alarm:
        if 'p2' in locals():
            p2.kill()
        else:
            p1.kill()
        msg = "Running more than {0} secs to run cmd: {1}".format(timeout_secs, cmds)
        if abort:
            error(msg)
        else:
            warn(msg)
            raise
    except:
        msg = "Failed to run cmd: {0}\n{1}".format(cmds, sys.exc_info()[1:2])
        if abort:
            error(msg)
        else:
            warn(msg)
            raise
    finally:
        if timeout:
            signal.alarm(0)


def run_cmd_as_user(*cmds, **kwargs):
    """run cmd as non-root user
    Args:
        *cmds
            cmd1        (list): cmd to run
            cmd2        (list): (optional) cmd piped; cmd1 | cmd2
        **kwargs
            user         (str): (default="oracle") os user to run cmd
            envs         (ENV): ENV = os.environ.copy()
            abort       (bool): (default=False) if True, abort on errors. If False, warn on errors
            timeout     (bool): (default=True) to timeout when running longer than ALARM_TIMEOUT or timeout_secs
            timeout_secs (int): (default=30) timeout in sec
    Returns:
        str: cmds output if succeeded, or exit if erred and abort is True
    Raises:
        Exception:  invalid cmd/subprocess/timeout errors
    """
    try:
        if kwargs.get("user", None) is None:
            kwargs["user"] = "oracle"

        return run_cmd(*cmds, **kwargs)

    except:
        raise


def grep_cmd(*cmds, **kwargs):
    """grep cmd wrapper of run_cmd/run_cmd_as_user
    Args:
        *cmds
            cmd1    (list): cmd to run
            cmd2    (list): (optional) cmd piped; cmd1 | cmd2

        **kwargs
            user     (str): os user to run cmd
            envs     (ENV): ENV = os.environ.copy()
            abort   (bool): (default=False) if True, abort on errors. If False, warn on errors
            timeout (bool): (default=True) to timeout when running longer than ALARM_TIMEOUT

    Returns:
        str: cmd output, exit if erred and abort is True
    Raises:
        Exception: invalid cmd/subprocess/timeout errors
    """
    try:
        grep_cmd_flag = False
        for cmd in cmds:
            if "grep" in cmd[0]:
                grep_cmd_flag = True

        if not grep_cmd_flag:
            raise ValueError("Not a grep cmd: {0}".format(cmds))

    except ValueError as msg:
        warn(msg)
        raise
    except:
        msg = "Failed to run cmd: {0}\n{1}".format(cmds, sys.exc_info()[1:2])
        warn(msg)
        raise

    try:
        if "user" in kwargs:
            return run_cmd_as_user(*cmds, **kwargs)
        else:
            return run_cmd(*cmds, **kwargs)
    except ValueError as msg:
        matched = re.search(r"returncode=1!\n(.*)", str(msg))
        if matched:
            return matched.group(1)
        else:
            warn(msg)
            raise
    except:
        raise


def send_email(recipient, subject, email_body, attachements=None, sender=None):
    """Send an HTML email with an embedded image and a plain text message for
    email clients that don't want to display the HTML
    Args:
        recipient     (str): recipient
        subject       (int): subject
        email_body    (str): email body
        attachements (list): attachement, e.g., [logfile1, logfile2]
    Returns:
        bool: True if succeeded
    Raises:
        Exception:  smtp.sendmail error
    """
    import smtplib
    from email.MIMEMultipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    from email.MIMEText import MIMEText
    from email.MIMEImage import MIMEImage

    try:
        if sender is None:
            sender = "no.reply@oracle.com"

        # Create the root message and fill in the from, to, and subject headers
        msg_root = MIMEMultipart("related")
        msg_root["Subject"] = subject
        msg_root["From"] = sender
        msg_root["To"] = recipient
        msg_root.preamble = "This is a multi-part message in MIME format."

        # Encapsulate the plain and HTML versions of the message body in an
        # 'alternative' part, so message agents can decide which they want to display.
        msg_alternative = MIMEMultipart("alternative")
        msg_root.attach(msg_alternative)

        msg_text = MIMEText(email_body)
        msg_alternative.attach(msg_text)

        # Reference the image in the IMG SRC attribute by the ID
        msg_text = MIMEText("<br>{0}<br><br><img src='cid:image1'>".format(email_body), "html")
        msg_alternative.attach(msg_text)

        # Open the image in the current directory
        fp = open("{0}/email_header.jpg".format(os.path.dirname(__file__)), "rb")
        msg_image = MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        msg_image.add_header("Content-ID", "<image1>")
        msg_root.attach(msg_image)

        for f in attachements or []:
            basename_f = os.path.basename(f)
            with open(f, "rb") as fil:
                part = MIMEApplication(fil.read(), Name=basename_f)

            part['Content-Disposition'] = 'attachment; filename="%s"' % basename_f
            msg_root.attach(part)

        smtp = smtplib.SMTP("localhost")
        smtp.sendmail(sender, recipient, msg_root.as_string())
        smtp.quit()
        return True
    except:
        msg = "Failed to send email!\n{0}".format(sys.exc_info()[1:2])
        warn(msg)
        raise


"""User/Process checking functons"""
def check_already_running(script_name):
    """check if script is already running
    Args:
        script_name (str): script name; i.e. main calling script
    Returns:
        None: exit if script is already running
    Raises:
        Exception: run_cmd error
    """
    try:
        # the last char is removed to handle either .py or .pyc
        basename_with_ext = os.path.basename(script_name[:-1])
        cmd1 = ["ps", "aux"]
        cmd2 = ["grep", "-c", grep_bracket(basename_with_ext)]
        out = run_cmd(cmd1, cmd2)

        if int(out) > 1:
            error("%s is already running!" % script_name)
    except:
        raise


def check_process(process_):
    """check if process is running
    Args:
        process_ (str): process name
    Returns:
        bool: True if ps count >= 1
    Raises:
        Exception: run_cmd error
    """
    try:
        cmd1 = ["ps", "aux"]
        cmd2 = ["grep", "-c", grep_bracket(process_)]
        out = run_cmd(cmd1, cmd2)

        if int(out) >= 1:
            return True
        else:
            return False
    except:
        raise


def check_int(s):
    """check int
    Args:
        s (str): numeric str
    Returns:
        bool: True if int(s)
    """
    try:
        int(s)
        return True
    except ValueError:
        return False


def check_root():
    """check root user
    Args:
    Returns:
        None: exit if not root
    """
    if os.geteuid() != 0:
        error("Script must be run as root!")


def check_user(user):
    """check if user == "os user"
    Args:
        user (str): user to check
    Returns:
        bool: True if user == "os user"
    """
    try:
        pwd.getpwnam(user)
    except KeyError:
        warn("User %s doesn't exist!" % user)
        return False

    os_user = getuser()
    if user == os_user:
        return True
    else:
        warn("Current os user %s is not %s!" % (os_user, user))
        return False


def get_uid(user):
    """get uid of user
    Args:
        user (str): username
    Returns:
        tuple: (uid, gid)
    """
    try:
        uid = pwd.getpwnam(user).pw_uid
        gid = pwd.getpwnam(user).pw_gid
        return uid, gid
    except:
        warn(sys.exc_info()[1:2])
        return None, None


def kill_ospid(ospid, hostname=None):
    """kill -9 ospid
    Args:
        ospid    (int): ospid
        hostname (str): (default=None) returns localhost dbsid
    Returns:
        bool: True if succeeded
    Raises:
        Exception: run_cmd error
    """
    try:
        if hostname:
            cmd = ["/usr/bin/ssh", hostname, "kill", "-9", str(ospid)]
        else:
           cmd = ["kill", "-9", str(ospid)]

        out = run_cmd(cmd)
        info("{0} completed successfully - {1}".format(sys._getframe(1).f_code.co_name, cmd))
        return True
    except:
        raise


def set_uid(uid, gid):
    """set uid while running process as a different user
    Args:
        uid (int): uid
        gid (int): gid
    Returns:
        None
    """
    def _set_uid():
        os.setgid(gid)
        os.setuid(uid)
    return _set_uid

"""timezone functions"""
def get_utc_offset():
    """get utc offset in hours
    Args:
    Returns:
        int: DST adjusted utc offset in minus hours
    """
    offset_secs = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    offset = offset_secs / 60 / 60 * -1
    return offset


def get_utc_time(datetime_str, datetime_fmt):
    """get utc time from local input datetime
    Args:
        datetime_str (str): datetime str
        datetime_fmt (str): datetime format, e.g., "%Y-%m-%d %H:%M:%S"
    Returns:
        datetime: utc time
    """
    try:
        local_time = datetime.strptime(datetime_str, datetime_fmt)
        utc_offset = get_utc_offset()
        utc_time = local_time - timedelta(hours=utc_offset)
        return utc_time
    except:
        msg = "Failed to parse datetime!\n{0}".format(sys.exc_info()[1:2])
        warn(msg)
        raise


def get_datetime_from_epoch(epoch_time):
    """get datetime from epoch time
    Args:
        epoch_time (int): epoch time
    Returns:
        str: str in "%Y-%m-%d %H:%M:%S" format
    """
    try:
        dt = datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")
        return dt
    except:
        msg = "Failed to parse epoch time!\n{0}".format(sys.exc_info()[1:2])
        warn(msg)
        raise


def get_epoch_from_datetime(datetime_str, datetime_fmt):
    """get epoch time from datetime
    Args:
        datetime_str (str): datetime str
        datetime_fmt (str): datetime format, e.g., "%Y-%m-%d %H:%M:%S"
    Returns:
        int: epoch time in secs
    """
    try:
        dt = datetime.strptime(datetime_str, datetime_fmt)
        epoch_secs = int(dt.strftime("%s"))
        return epoch_secs
    except:
        msg = "Failed to get epoch time!\n{0}".format(sys.exc_info()[1:2])
        warn(msg)
        raise

def get_free_space(dirname):
    """get free space
    Args:
        dirname (str): target dir
    Returns:
        str: available space, e.g. 123G
    Raises:
        Exception: run_cmd error
    """
    if not dir_exists(dirname):
        return None

    try:
        cmd = ["/bin/df", "-PhT", dirname]
        out = run_cmd(cmd)
        out_list = out.split("\n")

        # Parse the first line to find the position of the Avail column
        # and then retrieve the value from that position in the next line
        avail_index = out_list[0].split().index("Avail")
        avail_space = out_list[1].split()[avail_index]
        return avail_space
    except:
        msg = "Failed to get free space of {0}!\n{1}".format(dirname, sys.exc_info()[1:2])
        warn(msg)


def get_used_space(dirname):
    """get used space percent
    Args:
        dirname (str): dirname
    Returns:
        int: used space percent
    Raises:
        Exception: run_cmd error
    """
    if not dir_exists(dirname):
        return None

    try:
        cmd = ["/bin/df", "-PhT", dirname]
        out = run_cmd(cmd)
        out_list = out.split("\n")

        # Parse the first line to find the position of the Use% column
        # and then retrieve the value from that position in the next line
        used_index = out_list[0].split().index("Use%")
        used_percent = int(out_list[1].split()[used_index][:-1])
        return used_percent
    except:
        msg = "Failed to get space used% of {0}!\n{1}".format(dirname, sys.exc_info()[1:2])
        warn(msg)


def get_dir_size_mb(dirname):
    """get directory size in MB
    Args:
        dirname (str): dirname
    Returns:
        int: directory size in MB
    Raises:
        Exception: run_cmd error
    """
    if not dir_exists(dirname):
        return None

    try:
        cmd = ["/usr/bin/du", "-sB", "M", dirname]
        out = run_cmd(cmd)
        dir_size = int(out.split()[0][:-1])
        return dir_size
    except:
        msg = "Failed to get directory size of {0}!\n{1}".format(dirname, sys.exc_info()[1:2])
        warn(msg)


def get_hostname(fqdn=False):
    """get hostname
    Args:
        fqdn (str): hostname w/o domain if fqdn=False
    Returns:
        str: hostname
    """
    try:
        if fqdn:
            _hostname = os.uname()[1]
        else:
            _hostname = os.uname()[1].split(".")[0]

        return _hostname
    except:
        error("Failed to get hostname!")


def grep_bracket(str_arg):
    """get bracketed str, e.g. [p]mon
    Args:
        str_arg (str): str arg
    Returns:
        str: bracketed str
    """
    if len(str_arg) == 1:
        bracketed_str = "[{0}]".format(str_arg[0])
    else:
        bracketed_str = "[{0}]{1}".format(str_arg[0], str_arg[1:])

    return bracketed_str


def get_os_sep_path(path_):
    """get path containing '\' or '/' replaced with os.sep
    Args:
        path_ (str): path str
    Returns:
        str: path replaced with os.sep
    """
    if path_:
        return str(path_.replace('\\', os.sep).replace(r'/', os.sep))

def read_json(json_file, ordered=False):
    """read json file
    Args:
        json_file (str): json file
        ordered  (bool): (default=False) True for ordered read
    Returns:
        dict: json data
    """
    try:
        with open(json_file, "r") as f:
            if ordered:
                 _json_dict = json.load(f, object_pairs_hook=OrderedDict)
            else:
                _json_dict = json.load(f)

            return _json_dict
    except:
        msg = "{0}".format(sys.exc_info()[1:2])
        warn(msg)
        raise


def write_json(json_data, json_file):
    """write json file
    Args:
        json_data (dict): json data
        json_file  (str): json filename in full path
    Returns:
        bool: True if succeeded
    """
    try:
        if not type(json_data) is dict and not isinstance(json_data, OrderedDict):
            raise ValueError("type(json_data) needs to be dict!")

        with open(json_file, "w") as f:
            json_str = json.dumps(json_data, indent=4, separators=(",", ": "), ensure_ascii=False)
            f.write(json_str)
            return True

    except ValueError as msg:
        warn(msg)
        raise
    except:
        msg = "{0}".format(sys.exc_info()[1:2])
        warn(msg)
        raise

"""OS load functions"""
def get_cpuutil():
    """get cpu average utilization during the last 3 seconds
    Args:
    Returns:
        float: cpuutil (0 <= cpuutil < 1)
    Raises:
        Exception: /proc/stat read error
    """
    try:
        with open('/proc/stat') as f:
            for line in f:
                line = line.split()
                if line[0] == 'cpu':
                    pre_list = list(map(lambda x: float(x), line[1:]))
                    preuser = pre_list[0]
                    prenice = pre_list[1]
                    presystem = pre_list[2]
                    preidle = pre_list[3]
                    preiowait = pre_list[4]
                    preirq = pre_list[5]
                    presoftirq = pre_list[6]
                    break
        if preuser and preuser >= 0:
            total1 = preuser + prenice + presystem + preidle + preiowait + preirq + presoftirq
            # os_check_metrics['cpu']['totalprev'] = total1
            # os_check_metrics['cpu']['idleprev'] = preidle

        time.sleep(3)

        with open('/proc/stat') as f:
            for line in f:
                line = line.split()
                if line[0] == 'cpu':
                    cur_list = list(map(lambda x: float(x), line[1:]))
                    curuser = cur_list[0]
                    curnice = cur_list[1]
                    cursystem = cur_list[2]
                    curidle = cur_list[3]
                    curiowait = cur_list[4]
                    curirq = cur_list[5]
                    cursoftirq = cur_list[6]
        if curuser and curuser >= 0:
            total2 = curuser + curnice + cursystem + curidle + curiowait + curirq + cursoftirq
            # os_check_metrics['cpu']['totalcur'] = total2
            # os_check_metrics['cpu']['idlecur'] = curidle

        if total2 > total1:
            cpuutil = 1 - (curidle - preidle) / (total2 - total1)
            # print "cpu utilization: ", cpuutil
            # os_check_metrics['cpu']['cpuutil'] = cpuutil
        elif total2 == total1:
            cpuutil = 0
        else:
            raise ValueError("/proc/stat cpu values({0} > {1}) are invalid!".format(total1, total2))

        return cpuutil

    except:
        message = "Failed to run get_cpuutil!\n{0}".format(sys.exc_info()[1:2])
        warn(message)
        raise


def get_loadavg():
    """get loadavg of the last 1, 5, and 15 minutes
    Args:
    Returns:
        list: list, e.g. [8.62, 8.62, 9.31]
    Raises:
        Exception: OSError error
    """
    try:
        return list(os.getloadavg())
    except:
        message = "Failed to run get_loadavg!\n{0}".format(sys.exc_info()[1:2])
        warn(message)
        raise


def get_meminfo():
    """get meminfo by reading /proc/meminfo
    Args:
    Returns:
        list: [float(memutil), float(swaputil)]
    Raises:
        Exception: /proc/meminfo read error
    """
    try:
        meminfo = {}
        with open('/proc/meminfo') as f:
            for line in f:
                line_list = line.split()
                meminfo[line_list[0]] = line_list[1]

        MemFree = float(meminfo['MemFree:'])
        MemTotal = float(meminfo['MemTotal:'])
        SwapFree = float(meminfo['SwapFree:'])
        SwapTotal = float(meminfo['SwapTotal:'])
        MemUtil = 1 - MemFree / MemTotal
        SwapUtil = 1 - SwapFree / SwapTotal

        return [MemUtil, SwapUtil]

    except:
        message = "Failed to run get_meminfo!\n{0}".format(sys.exc_info()[1:2])
        warn(message)
        raise


def check_os_load():
    """check OS high load. dbhealing workflows use this function to check OS resource contention.
    Args:
    Returns:
        bool: True if cpu util > 98% or loadavg > 500 or memfree/memtotal < 5% or swapfree/swaptotal < 5%
    Raises:
        Exception: get_cpuutil()/get_loadavg()/get_meminfo() exceptions
    """
    try:
        cpuutil = get_cpuutil()
        loadavg_list = get_loadavg()
        loadavg = (loadavg_list[0] + loadavg_list[1] + loadavg_list[2]) / 3
        memusage = get_meminfo()

        # if cpuutil > 98% or loadavg > 500 or used memory > 95% or swapspace > 95%
        if cpuutil > 0.98 or loadavg > 500 or memusage[0] > 0.95 or memusage[1] > 0.95:
            return True
        else:
            return False

    except:
        message = "Failed to run check_os_load!\n{0}".format(sys.exc_info()[1:2])
        warn(message)
        raise

def _log_msg(level, msg):
    """log msg to stdout and logger
    Args:
        level (str): log level
        msg   (str): message
    Returns:
        None: exit if level == "ERROR"
    """

    if logger is not None:
        getattr(logger, level.lower())(msg.replace('\\n', '\n'))

    if level == "DEBUG":
        pass
    else:
        if level=="INFO":
            color=colors.green
        if level=="WARN":
            color=colors.orange
        if level=="ERROR":
            color=colors.red
        print(color,"[{0:4}]".format(level),colors.reset,msg.replace('\\n', '\n'))


def _p(var):
    """print wrapper for debug
    Args:
        var (obj): var
    Returns:
        None
    """
    print("\ntest: {0} {1}\n".format(type(var), repr(var)))


def _umask(filename_):
    """chmod tempfile to 644
    Args:
        filename_ (str): filename to chmod
    Returns:
        None
    """
    umask = os.umask(0)
    os.umask(umask)
    os.chmod(filename_, 0o644 & ~umask)
