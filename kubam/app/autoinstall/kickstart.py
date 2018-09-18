from subprocess import call
from config import Const


class Kickstart(object):
    """
    This script builds a kickstart image in the /kubam directory.
    Build the kickstart images and return error code with a message.
    """
    @staticmethod
    def build_boot_image(node, template):
        new_image_name = Const.KUBAM_DIR + node["name"] + ".img"
        new_image_dir = Const.KUBAM_DIR + node["name"]

        # Copy the file to the directory.
        o = call(["cp", "-f", Const.BASE_IMG, new_image_name])
        if not o == 0:
            return 1, "not able to copy {0} to {1}".format(Const.BASE_IMG, new_image_name)

        # Create mount point
        o = call(["mkdir", "-p", new_image_dir])
        if not o == 0:
            return 1, "not able to call 'mkdir -p {0}'".format(new_image_dir)

        # Use fuse to mount the image, e.g: fuseext2 kube01.img kube01 -o rw+,nonempty
        o = call(["fuseext2", "-o", "rw+,nonempty", new_image_name, new_image_dir])
        if not o == 0:
            return 1, "not able to run fuseext2 -o rw+,nonempty {0} {1}".format(new_image_name, new_image_dir)

        # Write the file over the existing file if it exists. Hack to over write file
        fw = new_image_dir + "/ks1.cfg"
        fw_real = new_image_dir + "/ks.cfg"
        try:
            with open(fw, 'w') as f:
                f.write(template)
        except IOError as err:
            print err.strerror
            return 1, "{0}".format(err.strerror)

        # Move this file to ks.cfg
        o = call(["mv", fw, fw_real])
        if not o == 0:
            return 1, "unable to run: mv {0} {1}".format(fw, fw_real)

        # Unmount the filesystem.
        o = call(["umount", new_image_dir])
        if not o == 0:
            pass  # we had a case in ubuntu where this gave an error and still worked.
            # return 1, "unable to unmount {0}".format(new_image_dir)

        # Remove mount directory
        o = call(["rm", "-rf", new_image_dir])
        if not o == 0:
            return 1, "unable to rm -rf {0}".format(new_image_dir)
        return 0, None
