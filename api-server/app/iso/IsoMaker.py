#!/usr/bin/env python
import os, re

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
def extract_iso(iso, mnt_dir):
    err = 0
    os.mkdir(mnt_dir)
    return "", err

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
    
     

   
