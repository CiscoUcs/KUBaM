import os
import re
import random
import string
import subprocess 
from shutil import rmtree
from config import Const


class IsoMaker(object):
    @staticmethod
    def list_isos(directory):
        """
        Takes in a hash of configuration data and validates to make surecit has the stuff we need in it.
        :param directory:
        :return: err, array
        """
        # Get all ISOs in a directory
        r = re.compile("iso$", re.IGNORECASE)

        try:
            files = os.listdir(directory)
        except OSError as err:
            return 1, err.strerror + ": " + err.filename
        list_of_isos = filter(r.search, files)
        return 0, list_of_isos

    @staticmethod
    def extract_isos(isomap):
        for o in isomap:  
            os_dir = "/kubam/" + Const.OS_DICT[o['os']]['dir']
            if not os.path.isdir(os_dir):
                err, msg = IsoMaker.extract_iso(o['file'], os_dir)
                if err != 0:
                    return err, msg
                err, msg = IsoMaker.refine_extracted(o['os'], os_dir)
                if err != 0:
                    return err, msg
        return 0, None

    @staticmethod
    def refine_extracted(osname, mnt_dir):
        """
        Given an os and an extracted OS directory do any updates that need to be
        done in this directory.  For now this is mostly for RHVH4.1 that needs to be refined.
        specifically: get the correct squashfs file as shown in 5.2.2 step 3 here:
        https://access.redhat.com/documentation/en-us/red_hat_virtualization/4.1/html-single/installation_guide/#part-Installing_Hypervisor_Hosts
        """
        if not osname in ['rhvh4.1','rhvh4.3']:
            return 0, None 
        os.chdir(mnt_dir)
        files = [x for x in os.listdir("Packages") if x.startswith("redhat-virtualization-host-image-update")]
        if len(files) < 1:
            return 1, "Unable to find redhat-virtualization-host-image-update package in source" 
        #o = call(["rpm2cpio", "Packages/" + files[0], "|", "cpio", "-idmv"])
        ps = subprocess.Popen(('rpm2cpio', 'Packages/' + files[0]), stdout=subprocess.PIPE)
        output = subprocess.check_output(('cpio', '-idmv'), stdin=ps.stdout)
        ps.wait()
        #if not o == 0:
        #    return 1, "Unable to extract virtualization host image from rhvh4.1 iso directory" 
        files = [x for x in os.listdir(mnt_dir + "/usr/share/redhat-virtualization-host/image") if x.endswith("squashfs.img")]
        if len(files) < 1:
            return 1, "Unable to find squashfs image" 
        o = subprocess.call(["mv", "usr/share/redhat-virtualization-host/image/" + files[0], mnt_dir + "/squashfs.img"])
        if not o == 0:
            return 1, "Unable to move extracted virtualization host squashfs.img" 
        return 0, None
        

    @staticmethod
    def extract_iso(iso, mnt_dir):
        """
        Extract the ISO file into a directory call with iso file and directory to mount in:
        :param iso: /kubam/CentOS-7-x86_64-Minimal-1611.iso
        :param mnt_dir: /kubam/centos7.3
        :return: error code and message
        """
        err = 0
        if os.path.isdir(mnt_dir):
            return 1, mnt_dir + " directory already exists."
        if not os.path.isfile(iso):
            return 1, "iso file {0} not found".format(iso)
        # osirrox -prog kubam -indev ./*.iso -extract . centos7.3
        
        o = subprocess.call(["osirrox", "-acl", "off", "-prog", "kubam", "-indev", iso, "-extract", ".", mnt_dir])
        if not o == 0:
            return 1, "error extracting ISO file.  Bad ISO file?"
        return err, "success"

    #  Change directory into the OS directory and determine what OS it actually is.
    @staticmethod
    def get_os(os_dir, iso):
        fname = os_dir + "/" + Const.OS_DICT[iso['os']]['key_file']
        if os.path.isfile(fname):
            f = object()
            try:
                f = open(fname, 'r')
            except OSError as err:
                # Permission denied error on ISO image.
                if err.errno == 13:
                    subprocess.call(["chmod", "-R", "0755", os_dir])
                    subprocess.call(["chmod", "0755", fname])
                    f = open(fname, "r")

            for line in f:
                if re.search(Const.OS_DICT[iso['os']]['key_string'], line):
                    return Const.OS_DICT[iso['os']]
        return None

    @staticmethod
    def mkboot_centos(os_name, version):
        boot_iso = "/kubam/" + os_name + version + "-boot.iso"
        if os.path.isfile(boot_iso):
            return 0, "boot iso was already created"
        os_dir = "/kubam/" + os_name + version
        stage_dir = "/kubam/tmp/" + str().join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
        o = subprocess.call(["mkdir", "-p", stage_dir])
        if not o == 0:
            return 1, "Unable to make directory " + stage_dir
        o = subprocess.call(["cp", "-a", os_dir + "/isolinux", stage_dir])
        if not o == 0:
            return 1, "Unable to copy /isolinux to {0}".format(stage_dir)
        o = subprocess.call(["cp", "-a", os_dir + "/.discinfo", stage_dir + "/isolinux/"])
        if not o == 0:
            return 1, "Unable to copy /.discinfo to {0}".format(stage_dir)
        o = subprocess.call(["cp", "-a", os_dir + "/LiveOS", stage_dir + "/isolinux/"])
        if not o == 0:
            return 1, "Unable to copy /LiveOS to {0}".format(stage_dir)
        o = subprocess.call(["cp", "-a", os_dir + "/images/", stage_dir + "/isolinux/"])
        if not o == 0:
            return 1, "Unable to copy /images/ to {0}".format(stage_dir)
        o = subprocess.call(["cp", "-a", "/usr/share/kubam/stage1/"+os_name+version+"/isolinux.cfg", stage_dir + "/isolinux/"])
        if not o == 0:
            return 1, "Unable to copy /isolinux.cfg to {0}".format(stage_dir)

        os.chdir("/kubam")
        o = 0
        if os_name == "centos":
            o = subprocess.call([
                "mkisofs", "-o", boot_iso, "-b", "isolinux.bin", "-c", "boot.cat", "-no-emul-boot", "-V",
                "CentOS 7 x86_64", "-boot-load-size", "4", "-boot-info-table", "-r",
                "-J", "-v", "-T", stage_dir + "/isolinux"
            ])
        elif os_name == "redhat":
            o = subprocess.call([
                "mkisofs", "-o", boot_iso, "-b", "isolinux.bin", "-c", "boot.cat", "-no-emul-boot", "-V",
                "RHEL-" + version + " Server.x86_64", "-boot-load-size", "4", "-boot-info-table", "-r",
                "-J", "-v", "-T", stage_dir + "/isolinux"
            ])

        elif os_name == "rhvh":
            o = subprocess.call([
                "mkisofs", "-o", boot_iso, "-b", "isolinux.bin", "-c", "boot.cat", "-no-emul-boot", "-V",
                "RHVH-" + version + " RHVH.x86_64", "-boot-load-size", "4", "-boot-info-table", "-r",
                "-J", "-v", "-T", stage_dir + "/isolinux"
            ])
        

        if not o == 0:
            return 1, "mkisofs failed for {0}".format(boot_iso)
        return 0, "success"

    @staticmethod
    def mkboot_esxi():
        boot_iso = "/kubam/esxi6.5-boot.iso"
        if os.path.isfile(boot_iso):
            return 0, "boot iso was already created"
        os_dir = "kubam/esxi6.5"
        # Overwrite the boot directory
        o = subprocess.call(["cp", "-a", "/usr/share/kubam/stage1/esxi6.5/BOOT.CFG", os_dir])
        if not o == 0:
            return 1, "Unable to copy /usr/share/kubam/stage1/esxi6.5/BOOT.CFG to {0}".format(os_dir)

        os.chdir("/kubam")
        # https://docs.vmware.com/en/VMware-vSphere/6.5/com.vmware.vsphere.install.doc/GUID-C03EADEA-A192-4AB4-9B71-9256A9CB1F9C.html
        o = subprocess.call([
            "mkisofs", "-relaxed-filenames", "-J", "-R", "-o", boot_iso, "-b", "ISOLINUX.BIN", "-c", "boot.cat",
            "-no-emul-boot", "-boot-load-size", "4", "-boot-info-table", "-no-emul-boot", os_dir
        ])
        if not o == 0:
            return 1, "Unable to create ISO image"

        return 0, "success"
    
    @staticmethod
    def mkboot_winpe():
        """ 
        check that winpe is there as this is a seperate step
        """
        if not os.path.isfile("/kubam/WinPE_KUBAM.iso"):
            return 1, "KUBAM WinPE_KUBAM.iso file not found.  This is a separate step. See: https://ciscoucs.github.io/site/kubam/configure/windows2.html"
        return 0, "success"

    @staticmethod
    def mkboot(oper_sys):
        if oper_sys == "centos7.3":
            return IsoMaker.mkboot_centos("centos", "7.3")
        elif oper_sys == "centos7.4":
            return IsoMaker.mkboot_centos("centos", "7.4")
        elif oper_sys == "centos7.5":
            return IsoMaker.mkboot_centos("centos", "7.5")
        elif oper_sys == "redhat7.2":
            return IsoMaker.mkboot_centos("redhat", "7.2")
        elif oper_sys == "redhat7.3":
            return IsoMaker.mkboot_centos("redhat", "7.3")
        elif oper_sys == "redhat7.4":
            return IsoMaker.mkboot_centos("redhat", "7.4")
        elif oper_sys == "redhat7.5":
            return IsoMaker.mkboot_centos("redhat", "7.5")
        elif oper_sys == "redhat7.6":
            return IsoMaker.mkboot_centos("redhat", "7.6")
        elif oper_sys == "rhvh4.1":
            return IsoMaker.mkboot_centos("rhvh", "4.1")
        elif oper_sys == "rhvh4.3":
            return IsoMaker.mkboot_centos("rhvh", "4.3")
        elif oper_sys in ["win2016", "win2012r2"]:
            return IsoMaker.mkboot_winpe()
        return 0, "success"
    
    @staticmethod
    def mkboot_isos(isos):
        """
        Make boot isos for all images. 
        """
        for iso in isos:
            err, msg = IsoMaker.mkboot(iso["os"])
            if err != 0:
                return err, msg
        return 0, None
    
        
    @staticmethod
    def mkboot_iso(isos):
        """
        Determine version of OS and make boot dir.
        :param isos: ISO images list
        :return: success or failure along with message
        """
        # Create random temporary directory
        err = 0
        msg = None
        for iso in isos:
            tmp_dir = "/kubam/tmp/"
            tmp_dir += str().join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            err, err_msg = self.extract_iso(iso['file'], tmp_dir)
            if err != 0:
                return err_msg, err
            o = self.get_os(tmp_dir, iso)
            if not o:
                return 1, "OS could not be determined with ISO image. Perhaps this is not a supported OS?"
            if not o["dir"] == iso["os"]:
                err_msg = "This ISO image seems to be {0} but you specified " \
                          "that it was {1}. Please change".format(o['dir'], iso['os'])
                return 1, err_msg
            # If the directory is already there, we don't touch it.
            if os.path.isdir("/kubam/" + o['dir']):
                print "removing temp"
                try:
                    rmtree(tmp_dir)
                except OSError as err:
                    # Permission denied error on ISO image.
                    if err.errno == 13:
                        subprocess.call(["chmod", "-R", "0755", tmp_dir])
                        rmtree(tmp_dir)
            else:
                print "creating " + o['dir']
                try:
                    os.rename(tmp_dir, "/kubam/" + o['dir'])
                except OSError as err:
                    # Permission denied error on ISO image.
                    if err.errno == 13:
                        subprocess.call(['chmod', '-R', '0755', tmp_dir])
                        os.rename(tmp_dir, "/kubam/" + o['dir'])
                    else:
                        return 1, err.strerror + ": " + err.filename

            # Now that we have tree, get boot media ready.
            err, msg = self.mkboot(o['dir'])
            # Remove tmp directory
            rmtree("/kubam/tmp")
        return err, msg
