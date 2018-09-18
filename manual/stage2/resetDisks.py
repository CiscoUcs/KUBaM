#!/usr/bin/env python

from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.ucsexception import UcsException
from urllib2 import HTTPError
from network import UCSNet
from server import UCSServer
from util import UCSUtil
import argparse
import os, sys

def ucs_login(username, password, server):
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

def ucs_logout(handle):
    handle.ucs_logout()



def main(): 
    global handle
    parser = argparse.ArgumentParser(description="Connect to UCS and set disks from 'JBOD' to 'configured good' on the servers you select.")
    parser.add_argument("user", help='The user account to log into UCS: e.g.: admin')
    parser.add_argument("password", help='The password to connect to UCS: e.g.: cisco123')
    parser.add_argument("server", help='UCS Manager: e.g: 192.168.3.1')
    args = parser.parse_args()
    handle = ucs_login(args.user, args.password, args.server) 
    servers = UCSServer.select_kube_servers(handle)
    for server in servers:
        UCSServer.reset_disks(handle,server)
    ucs_logout(handle)

if __name__ == '__main__':
    main()
