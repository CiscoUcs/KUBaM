import random
import string
import os
from subprocess import call
from config import Const


class VMware(object):
    """
    This class builds a ESXi kickstart image in the /kubam directory.
    Build an ISO image for each ESXi host
    """
    @staticmethod
    def build_boot_image(node, template):
        tmp_dir = Const.KUBAM_DIR + "tmp/"
        tmp_dir += str().join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        src_dir = Const.KUBAM_DIR + node["os"] + "/."

        if not os.path.isdir(src_dir):
            return 1, "source directory {0} not found.  Please extract ISO.".format(src_dir)

        o = call(["mkdir", "-p", tmp_dir])
        if not o == 0:
            return 1, "not able to run mkdir -p {0}".format(tmp_dir)

        # Create new stage directory
        o = call(["cp", "-a", src_dir, tmp_dir])
        if not o == 0:
            return 1, "not able to copy files from {0} to {1}".format(src_dir, tmp_dir)

        # Change access privileges just in case. Not sure why this happens with ESXi.
        o = call(["chmod", "-R", "0755", tmp_dir])
        if not o == 0:
            return 1, "not able to change access privileges to {0}".format(tmp_dir)

        # Copy over the BOOT.CAT file to add the kickstart directive.
        o = call(["cp", Const.KUBAM_SHARE_DIR + "/stage1/" + node["os"] + "/BOOT.CFG", tmp_dir + "/BOOT.CFG"])
        if not o == 0:
            return 1, "not able to copy kickstart directive"

        # Write the file over the existing file if it exists. Hack to over write file
        fw = tmp_dir + "/KS1.CFG"
        fw_real = tmp_dir + "/KS.CFG"
        try:
            with open(fw, 'w') as f:
                f.write(template)
        except IOError as err:
            print err.strerror
            return 1, "{0}".format(err.strerror)

        # Move this file to the real one
        o = call(["mv", fw, fw_real])
        if not o == 0:
            return 1, "unable to run: mv {0} {1}".format(fw, fw_real)

        # Zip it up
        cwd = os.getcwd()
        os.chdir("/kubam")
        o = call([
            "mkisofs", "-relaxed-filenames", "-J", "-R",
            "-o", node['name'] + ".iso", "-b", "ISOLINUX.BIN",
            "-c", "boot.cat", "-no-emul-boot", "-boot-load-size",
            "4", "-boot-info-table", "-no-emul-boot", tmp_dir
        ])
        if not o == 0:
            return 1, "mkisofs failed to make new boot image. See server logs"

        os.chdir(cwd)

        # Remove temporary directory
        o = call(["rm", "-rf", Const.KUBAM_DIR + "/tmp"])
        if not o == 0:
            return 1, "unable to rm -rf {0}".format(Const.KUBAM_DIR + "/tmp")
        return 0, None
