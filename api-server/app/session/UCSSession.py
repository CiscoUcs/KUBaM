from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.ucsexception import UcsException
import socket
from urllib2 import HTTPError
import os, sys

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
    return handle, ""

def logout(handle):
    handle.logout()
