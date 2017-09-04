#!/usr/bin/env python
# this script builds a kickstart image in the /kubam directory. 
import random, string, os
from subprocess import call
from shutil import rmtree



# constants.  
KUBAM_DIR="/kubam/"
KUBAM_SHARE_DIR="/usr/share/kubam/"
   

# build an ISO image for each ESXi host
def build_boot_image(node, template):
    tmp_dir = KUBAM_DIR + "tmp/" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    src_dir = KUBAM_DIR + node["os"] + "/."
   
    if not os.path.isdir(src_dir):
        return 1, "source directory %s not found.  Please extract ISO." % src_dir 

    o = call(["mkdir" , "-p", tmp_dir])
    if not o == 0: 
        return 1, "not able to run mkdir -p %s" % tmp_dir
    # create new stage directory 
    o = call(["cp" , "-a", 
                src_dir,
                tmp_dir])
    if not o == 0: 
        return 1, "not able to copy files from %s to %s" % (src_dir, tmp_dir)
    # now chmod just in case. Not sure why this happens with ESXi. 
    o = call(["chmod", "-R", "0755", tmp_dir])
   
    # Copy over the BOOT.CAT file to add the kickstart directive.
    o = call(["cp", KUBAM_SHARE_DIR + "/stage1/" + node["os"] + "/BOOT.CFG", tmp_dir + "/BOOT.CFG"])
 
    # write the file over the existing file if it exists. 
    # hack to over write file 
    fw = tmp_dir + "/KS1.CFG"
    fw_real = tmp_dir + "/KS.CFG"
    try: 
        with open(fw, 'w') as f:
            f.write(template)
    except IOError as err:
        return 1, "%s %s" % (err.strerror, file_name)

    # mv this file to the real one
    o = call(["mv", fw, fw_real])            
    if not o == 0:
        return 1, "unable to run: mv %s %s" % (fw, fw_real)

    # now we zip it up. 
    cwd = os.getcwd()
    os.chdir("/kubam")
    o = call(["mkisofs", "-relaxed-filenames", "-J", "-R", 
            "-o", node["name"] + ".iso", "-b", "ISOLINUX.BIN", 
            "-c", "boot.cat", "-no-emul-boot", "-boot-load-size",
            "4", "-boot-info-table", "-no-emul-boot", tmp_dir])
    if not o == 0:
        return 1, "mkisofs failed to make new boot image. See server logs"

    os.chdir(cwd)

    # remove tmp dir
    o = call(["rm", "-rf", KUBAM_DIR + "/tmp"])
    if not o == 0:
        return 1, "unable to rm -rf %s" % KUBAM_DIR + "/tmp"
    return 0, ""
