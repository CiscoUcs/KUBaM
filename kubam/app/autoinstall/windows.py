from subprocess import call
from config import Const


class Windows(object):
    """
    This script builds a windows autoinstall image in the /kubam directory.
    Build the autoinstall image and return error code with a message.
    """
    @staticmethod
    def build_boot_image(node, template, net_template):
        new_image_name = Const.KUBAM_DIR + node["name"] + ".img"
        new_image_dir = Const.KUBAM_DIR + node["name"]

        # Copy the file to the directory.
        o = call(["cp", "-f", Const.WIN_IMG, new_image_name])
        if not o == 0:
            return 1, "not able to copy {0} to {1}".format(Const.BASE_IMG, new_image_name)

        # Create mount point
        o = call(["mkdir", "-p", new_image_dir])
        if not o == 0:
            return 1, "not able to call 'mkdir -p {0}'".format(new_image_dir)

        fw = new_image_dir + "/autounattend.xml"
        try:
            with open(fw, 'w') as f:
                f.write(template)
        except IOError as err:
            print err.strerror
            return 1, "{0}".format(err.strerror)

        # Move this file to the fat filesystem
        o = call(["mcopy", "-o", "-i", new_image_name, fw, "::autounattend.xml"])
        if not o == 0:
            return 1, "unable to run: mcopy -o -i {0} {1} ::autounattend.xml".format(new_image_name, fw)

        # Write the file over the existing file if it exists. Hack to over write file
        fw = new_image_dir + "/network.txt"
        try:
            with open(fw, 'w') as f:
                f.write(net_template)
        except IOError as err:
            print err.strerror
            return 1, "{0}".format(err.strerror)

        # Move this file to ks.cfg
        o = call(["mcopy", "-o", "-i", new_image_name, fw, "::network.txt"])
        if not o == 0:
            return 1, "unable to run: mcopy -o -i  {0} {1} ::network.txt".format(new_image_name, fw)

        # Remove stage directory
        o = call(["rm", "-rf", new_image_dir])
        if not o == 0:
            return 1, "unable to rm -rf {0}".format(new_image_dir)
        return 0, None
