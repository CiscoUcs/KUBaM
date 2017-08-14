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
        sys.exit()
    except HTTPError as err:
        print "Connection Error: Bad UCSM? " + err.reason
        sys.exit()
    except:
        print "Issue logging in.  Please check that all parameters are correct"
        sys.exit()
    return handle

def logout(handle):
    handle.logout()
