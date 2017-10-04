#!/usr/bin/env python

from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.ucsexception import UcsException
from urllib2 import HTTPError
from network import UCSNet
from server import UCSServer
from session import UCSSession
from util import UCSUtil
import argparse
import os, sys

def main():
    global handle
    parser = argparse.ArgumentParser(description="Connect to UCS and create Kubernetes Infrastructure.  We will create several resources on your UCS domain that will help us install Kubernetes.")
    parser.add_argument("user", help='The user account to log into UCS: e.g.: admin') 
    parser.add_argument("password", help='The password to connect to UCS: e.g.: cisco123') 
    parser.add_argument("server", help='UCS Manager: e.g: 192.168.3.1') 
    parser.add_argument('-d', "--delete", help='Deletes kubernetes resources from UCS', action="store_true") 
    parser.add_argument('-D', "--domain", help='Adds a UCS domain for login', action="store_true") 
    parser.add_argument('-o', "--org", 
        type=str,
        default='root',
        help='The organization you want these resources created under: e.g: root')
        
    args = parser.parse_args()
    org = args.org
    # loging
    handle = UCSSession.login(args.user, args.password, args.server, args.domain)
    if handle == "":
        sys.exit(1)
    # see what's up with the org.
    if org == "":
        org = "org-root"
    else: 
        # verify org exists. 
        if UCSUtil.query_org(handle, org) == False:
            UCSUtil.create_org(handle, org)
        org = "org-root/org-" + org

    if args.delete == False:
        UCSNet.createKubeNetworking(handle, org)
        UCSServer.createKubeServers(handle, org)

    # destroy the UCS stuff we just created. 
    else: 
        print "Are you sure you want to delete the UCS Kubernetes infrastructure?"
        print "Running servers will be deleted, no work will be saved or recoverable."
        print "If this are in production, this could be really bad, and you might lose your job"
        val = raw_input("If you are really sure, please type: 'yes': ")
        if val == 'yes':
            UCSServer.deleteKubeServers(handle, org)
            UCSNet.deleteKubeNetworking(handle, org)
        else:
            print "cool.  No harm done."

    UCSSession.logout(handle)

if __name__ == '__main__':
    main()
