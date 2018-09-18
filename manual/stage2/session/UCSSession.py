from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.ucsexception import UcsException
from urllib2 import HTTPError
import os, sys

def login(username, password, server):
    handle = UcsHandle(server, username, password)
    try:
        handle.login()
    except UcsException as err:
        print "Login Error: " + err.error_descr
        return ""
    except HTTPError as err:
        print "Connection Error: Bad UCSM? " + err.reason
        return ""
    except:
        print "Issue logging in.  Please check that all parameters are correct"
        return ""
    return handle

def logout(handle):
    handle.ucs_logout()
