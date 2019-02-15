import random
import string
import os
from subprocess import call
from config import Const


class Ubuntu(object):
    """
    This class builds an Ubuntu boot image image in the /kubam directory for each node.
    """

    src_files = [
        "isolinux/f1.txt", 
        "isolinux/f2.txt", 
        "isolinux/f3.txt", 
        "isolinux/f4.txt", 
        "isolinux/f5.txt", 
        "isolinux/f6.txt", 
        "isolinux/f7.txt", 
        "isolinux/f8.txt", 
        "isolinux/f9.txt", 
        "isolinux/f10.txt", 
        "isolinux/splash.png",
        "isolinux/vesamenu.c32",
        "isolinux/stdmenu.cfg",
        "isolinux/rqtxt.cfg",
        "isolinux/prompt.cfg",
        "isolinux/menu.cfg",
        "isolinux/libutil.c32",
        "isolinux/libcom32.c32",
        "isolinux/ldlinux.c32",
        "isolinux/isolinux.bin",
        "isolinux/exithelp.cfg",
        "isolinux/boot.cat",
        "isolinux/adtxt.cfg",
        "install/netboot/ubuntu-installer/amd64/linux",
        "install/netboot/ubuntu-installer/amd64/initrd.gz",
        "boot"]



    @staticmethod
    def build_boot_image(node, preseed, initrd):
        """
        Builds the ISO image for the node (each has its own.)
        Put's the preseed file in the ubuntu18.04/preseed/<node>.seed
        """
        tmp_dir = Const.KUBAM_DIR + "tmp/"
        tmp_dir += str().join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        src_dir = Const.KUBAM_DIR + node["os"] + "/."

        if not os.path.isdir(src_dir):
            return 1, "source directory {0} not found.  Please extract ISO.".format(src_dir)

        o = call(["mkdir", "-p", tmp_dir])
        if not o == 0:
            return 1, "not able to run mkdir -p {0}".format(tmp_dir)

        # Create copy the files into this directory
        for f in Ubuntu.src_files:
            o = call(["cp", "-a", "{0}/{1}".format(src_dir, f) , tmp_dir])
            if not o == 0:
                return 1, "Not able to copy file from {0}/{1} to {2}. Make sure this is not the LiveCD and that you have the alternate installer CD.  See: ".format(src_dir, f, tmp_dir)

        # add the updated isolinux.cfg to the directory
        o = call(["cp", "-a", "/usr/share/kubam/stage1/ubuntu18.04/isolinux.cfg" , tmp_dir])
        if not o == 0:
            return 1, "not able to copy /usr/share/kubam/stage1/ubuntu18.04/isolinux.cfg to {0}".format(tmp_dir)

        # Write the txt.cfg file. 
        kp  = tmp_dir + "/txt.cfg"
        try:
            with open(kp, 'w') as f:
                f.write(initrd)
        except IOError as err:
            print err.strerror
            return 1, "{0}".format(err.strerror)

        # change access permissions
        o = call(["chmod", "-R", "0755", tmp_dir])
        if not o == 0:
            return 1, "not able to change access privileges to {0}".format(tmp_dir)

        # Make it into an iso now
        cwd = os.getcwd()
        os.chdir("/kubam")
        #mkisofs -D -r -V "UBUNTU" -cache-inodes -J -l -b isolinux.bin -c boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o ubuntu18.04-boot.iso ubuntu18.04-boot/
        o = call([
            "mkisofs", "-D", "-r", "-V", "UBUNTU", "-cache-inodes", "-J",
            "-l", "-b", "isolinux.bin", "-c", "boot.cat", "-no-emul-boot",
            "-boot-load-size", "4", "-boot-info-table", "-o", node['name'] + ".iso", tmp_dir
        ])
        if not o == 0:
            return 1, "mkisofs failed to make new boot image. See server logs"

        os.chdir(cwd)

        # Remove the temporary directory
        o = call(["rm", "-rf", Const.KUBAM_DIR + "/tmp"])
        if not o == 0:
            return 1, "unable to rm -rf {0}".format(Const.KUBAM_DIR + "/tmp")

        preseed_dir = Const.KUBAM_DIR + "/" + node['os'] + "/preseed/"
        o = call(["chmod", "-R", "0755", preseed_dir])
        if not o == 0:
            return 1, "not able to change access privileges to {0}".format(preseed_dir)

        # finally, write the preseed file in: 
        # /kubam/ubuntu18.04/preseed/<nodename>.seed
        pref = preseed_dir + node['name'] + ".seed"
        try: 
            with open(pref, 'w') as f:
                f.write(preseed)
        except IOError as err:
            print err.strerror
            return 1, "Can't create preseed file: {0}".format(err.strerror)
        
        return 0, None
