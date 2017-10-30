#!/usr/bin/env python
# this script builds a kickstart image in the /kubam directory. 
from subprocess import call

# constants.  
KUBAM_DIR="/kubam/"
KUBAM_SHARE_DIR="/usr/share/kubam/"
BASE_IMG=KUBAM_SHARE_DIR+"/stage1/ks.img"
    
# build the kickstart images
# return error code and message
def build_boot_image(node, template):
    new_image_name = KUBAM_DIR + node["name"] + ".img"
    new_image_dir = KUBAM_DIR + node["name"] 
    # cp the file to the directory. 
    o = call(["cp" , "-f", 
                BASE_IMG,
                new_image_name])
    if not o == 0: 
        return 1, "not able to copy %s to %s" % (BASE_IMG, new_image_name)
    # create mount point. 
    o = call(["mkdir" , "-p", new_image_dir])
    if not o == 0: 
        return 1 , "not able to call 'mkdir -p %s'" % new_image_dir
    # use fuse to mount the image. 
    # e.g: fuseext2 kube01.img kube01 -o rw+,nonempty
    o = call(["fuseext2", "-o", "rw+,nonempty",
                new_image_name, new_image_dir,])
    if not o == 0:
        return 1, "not able to run fuseext2 -o rw+,nonempty %s %s" % (new_image_name, new_image_dir)
    
    # write the file over the existing file if it exists. 
    # hack to over write file 
    fw = new_image_dir + "/ks1.cfg"
    fw_real = new_image_dir + "/ks.cfg"
    try: 
        with open(fw, 'w') as f:
            f.write(template)
    except IOError as err:
        print file_name, err.strerror
        return 1, "%s %s" % (err.strerror, file_name)

    # mv this file to ks.cfg
    o = call(["mv", fw, fw_real])            
    if not o == 0:
        return 1, "unable to run: mv %s %s" % (fw, fw_real)

    # unmount the filesystem. 
    o = call(["umount", new_image_dir])            
    if not o == 0:
        return 1, "unable to unmount %s" % new_image_dir
    # remove mount directory
    o = call(["rm", "-rf", new_image_dir])
    if not o == 0:
        return 1, "unable to rm -rf %s" % new_image_dir
    return 0, ""
