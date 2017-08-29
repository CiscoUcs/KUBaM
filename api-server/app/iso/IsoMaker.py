#!/usr/bin/env python
import os, re
from subprocess import call

# takes in a hash of configuration data and validates to make sure
# it has the stuff we need in it. 
# returns err, array. 
def list_isos(directory):
    # get all ISOs in a directory
    r = re.compile("iso$", re.IGNORECASE)
    files = []
    
    try:
        files = os.listdir(directory)
    except OSError as err:
        return 1, err.strerror + ": " + err.filename
    list_of_isos = filter(r.search, files)
    return 0, list_of_isos
   
#  extract the ISO file into a directory 
#  call with iso file and directory to mount in:
#   iso: /kubam/CentOS-7-x86_64-Minimal-1611.iso 
#   mnt_dir: /kubam/centos7.3 

def extract_iso(iso, mnt_dir):
    err = 0
    if os.path.isdir(mnt_dir):
        return 1, mnt_dir + " directory already exists."
    # osirrox -prog kubam -indev ./*.iso -extract . centos7.3
    o = call(["osirrox", "-prog", "kubam", "-indev", iso, "-extract",
                ".", mnt_dir])
    if not o == 0:
        return 1, "error extracting ISO file.  Bad ISO file?"
    return err, "success"

# cd into the OS directory and determine what OS it actually is. 
def get_os(os_dir):
    return 0    

# determine version of OS. 
def get_os_from_iso(iso):
    tmp_dir = "/tmp/" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))
    err_msg, err = extract_iso(iso, tmp_dir)
    if err != 0:
        return err_msg, err
    get_os(tmp_dir)
    
     

   
