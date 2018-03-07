#!/usr/bin/env python
import os, re
from subprocess import call
from shutil import rmtree
import random
import string

# dictionary of supported OSes
os_dict = {
    "centos7.3": {
        "key_file": ".discinfo",
        "key_string": "7.3",
        "dir": "centos7.3"
    },
    "centos7.4": {
        "key_file": ".discinfo",
        "key_string": "7.4",
        "dir": "centos7.4"
    },
    "redhat7.2": {
        "key_file": ".discinfo",
        "key_string": "7.2",
        "dir": "redhat7.2"
    },
    "redhat7.3": {
        "key_file": ".discinfo",
        "key_string": "7.3",
        "dir": "redhat7.3"
    },
    "redhat7.4": {
        "key_file": ".discinfo",
        "key_string": "7.4",
        "dir": "redhat7.4"
    },
    "esxi6.5" : {
        "key_file": ".DISCINFO",
        "key_string": "Version: 6.5.0",
        "dir": "esxi6.5"
    },
    "esxi6.0" : {
        "key_file": ".DISCINFO",
        "key_string": "Version: 6.0.0",
        "dir": "esxi6.0"
    }
}

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
    o = call(["osirrox", "-acl", "off", "-prog", "kubam", "-indev", iso, "-extract",
                ".", mnt_dir])
    if not o == 0:
        return 1, "error extracting ISO file.  Bad ISO file?"
    return err, "success"

# cd into the OS directory and determine what OS it actually is. 
def get_os(os_dir, iso):
    think_os = iso["os"]
    fname = os_dir + "/" + os_dict[iso["os"]]["key_file"]
    if os.path.isfile(fname):
        try: 
            f = open(fname, 'r')
        except OSError as err:
            # permission denied error on ISO image.
            if err.errno == 13:
                call(['chmod', '-R', '0755', os_dir])
                call(['chmod', '0755', fname])
                f = open(fname, 'r')
            
        for line in f:
            if re.search(os_dict[iso["os"]]["key_string"], line):
                return os_dict[iso["os"]]
    return {}

# mkboot for centos 
def mkboot_centos(os_name, version):
    boot_iso = "/kubam/" + os_name + version + "-boot.iso"
    if os.path.isfile(boot_iso):
        return 0, "boot iso was already created"
    os_dir = "kubam/" + os_name + version
    stage_dir = "/kubam/tmp/" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    o = call(["mkdir", "-p", stage_dir])
    if not o == 0:
        return 1, "Unable to make directory " + stage_dir
    o = call(["cp", "-a", os_dir + "/isolinux", stage_dir])
    o = call(["cp", "-a", os_dir + "/.discinfo", stage_dir + "/isolinux/"])
    o = call(["cp", "-a", os_dir + "/LiveOS", stage_dir + "/isolinux/"])
    o = call(["cp", "-a", os_dir + "/images/", stage_dir + "/isolinux/"])
    o = call(["cp", "-a", 
                "/usr/share/kubam/stage1/"+os_name+version+"/isolinux.cfg", 
                stage_dir + "/isolinux/"])

    os.chdir("/kubam")
    o = 0
    if os_name == "centos":
        o = call(["mkisofs", "-o", boot_iso, "-b", "isolinux.bin",
                "-c", "boot.cat", "-no-emul-boot", "-V",
                "CentOS 7 x86_64", "-boot-load-size" , "4", 
                "-boot-info-table", "-r", "-J", "-v", 
                "-T", stage_dir + "/isolinux"])
    elif os_name == "redhat":
        o = call(["mkisofs", "-o", boot_iso, "-b", "isolinux.bin",
                "-c", "boot.cat", "-no-emul-boot", "-V",
                "RHEL-"+version+" Server.x86_64", "-boot-load-size" , "4", 
                "-boot-info-table", "-r", "-J", "-v", 
                "-T", stage_dir + "/isolinux"])

    if not o == 0:
        return 1, "mkisofs failed for %s" % boot_iso
    return 0, "success"
    
def mkboot_esxi(version):
    boot_iso = "/kubam/esxi6.5-boot.iso"
    if os.path.isfile(boot_iso):
        return 0, "boot iso was already created"
    os_dir = "kubam/esxi6.5"
    # overwrite the boot directory
    o = call(["cp", "-a", 
                "/usr/share/kubam/stage1/esxi6.5/BOOT.CFG", 
                os_dir])

    os.chdir("/kubam")
    # https://docs.vmware.com/en/VMware-vSphere/6.5/com.vmware.vsphere.install.doc/GUID-C03EADEA-A192-4AB4-9B71-9256A9CB1F9C.html
    o = call(["mkisofs", "-relaxed-filenames", "-J", "-R", 
                "-o", boot_iso, "-b", "ISOLINUX.BIN",
                "-c", "boot.cat", "-no-emul-boot", 
                "-boot-load-size" , "4", 
                "-boot-info-table", "-no-emul-boot", os_dir])

    return 0, "success"
    


def mkboot(os):
    if os == "centos7.3":
        return mkboot_centos("centos", "7.3")
    elif os == "centos7.4":
        return mkboot_centos("centos", "7.4")
    elif os == "redhat7.2":
        return mkboot_centos("redhat", "7.2")
    elif os == "redhat7.3":
        return mkboot_centos("redhat", "7.3")
    elif os == "redhat7.4":
        return mkboot_centos("redhat", "7.4")
    return 0, "success"
    
# determine version of OS and make boot dir. 
# success:  return 0 and status message.
# failure:  return 1 and error message.
def mkboot_iso(isos):
    # create random tmp directory
    for iso in isos:
        tmp_dir = "/kubam/tmp/" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        err, err_msg = extract_iso(iso["file"], tmp_dir)
        if err != 0:
            return err_msg, err
        o = get_os(tmp_dir, iso)
        if not o:
            return 1, "OS could not be determined with ISO image.  Perhaps this is not a supported OS?"
        if not o["dir"] == iso["os"]:
            return 1, "This ISO image seems to be %s but you specified that it was %s.  Please change" % (o["dir"], iso["os"])
        # if the directory is already there, we don't touch it. 
        if os.path.isdir("/kubam/" + o["dir"]):
            print "removing temp"
            try:
                rmtree(tmp_dir) 
            except OSError as err:
                # permission denied error on ISO image.
                if err.errno == 13:
                    call(['chmod', '-R', '0755', tmp_dir])
                    rmtree(tmp_dir) 
        else:
            print "creating " + o["dir"]
            try: 
                os.rename(tmp_dir, "/kubam/" + o["dir"])
            except OSError as err:
                # permission denied error on ISO image.
                if err.errno == 13:
                    call(['chmod', '-R', '0755', tmp_dir])
                    os.rename(tmp_dir, "/kubam/" + o["dir"])
                else: 
                    return 1, err.strerror + ": " + err.filename
        
        # now that we have tree, get boot media ready. 
        err, msg = mkboot(o["dir"])
        # remove tmp directory
        rmtree("/kubam/tmp") 
    
    return err, msg
