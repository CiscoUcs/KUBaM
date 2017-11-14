from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.ucsexception import UcsException
import socket
from urllib2 import HTTPError
import os, sys

# get the current firmware version.  Returns something like: 3.1(2b)
def get_version(handle):
    from ucsmsdk.mometa.firmware.FirmwareRunning import FirmwareRunning
    dn = "sys/mgmt/fw-system"
    firmware = handle.query_dn(dn)
    return firmware.version

def ensure_version(handle):
    version = get_version(handle)
    if version.startswith('3'):
        return ""
    return "Unsupported UCS firmware version: %s.  Please update to at least 3.0" % version 


# returns handle, "error message"
def login(username, password, server):
    # first see if reachable
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        result = s.connect_ex((server, 80))
        if result != 0:
            return "", "%s is not reachable" % server
        s.close() 
    except socket.error as err:
        return "", "UCS Login Error: %s %s" % (server, err.strerror)

    handle = UcsHandle(server, username, password)
    try:
        handle.login()
    except UcsException as err:
        print "Login Error: " + err.error_descr
        return "", err.error_descr
    except HTTPError as err:
        print "Connection Error: Bad UCSM? " + err.reason
        return "", err.reason
    except:
        print "Issue logging in.  Please check that all parameters are correct"
        return "", "Issue logging in.  Please check that all parameters are correct."

    msg = ensure_version(handle)
    return handle, msg


def logout(handle):
    handle.logout()
