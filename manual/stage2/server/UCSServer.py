from ucsmsdk.ucsexception import UcsException
import re, sys

# given an array and a string of numbers, make sure they are all in the array:
# 
def check_values(array, csv):
    indexes = csv.split(',')
    for i in indexes:
        try: 
            i = int(i) - 1
        except:
            print "bad value: " + i
            return False
        if i < 0 or i > len(array) - 1:
            return False
    return True


# get the available servers to put in the pool. 
def select_kube_servers(handle):
    from ucsmsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
    from ucsmsdk.mometa.fabric.FabricComputeSlotEp import FabricComputeSlotEp
    print "Listing Available UCS Servers"
    filter_string = '(presence, "equipped")'
    # get blades
    blades = handle.query_classid("fabricComputeSlotEp", filter_string)
    # get all connected rack mount servers.
    servers = handle.query_classid("computeRackUnit")
    m = blades + servers
    while True:
        for i, s in enumerate(m):
            if type(s) is FabricComputeSlotEp:
                print "[%d]: Blade %s/%s type %s" % (i+1, s.chassis_id, s.rn, s.model)
            if type(s) is ComputeRackUnit:
                print "[%d]: Rack %s type %s" % (i+1, s.rn, s.model)
        vals = raw_input("(E.g.: 2,4,8): ")
        if check_values(m, vals) == True:
            k8servers = [m[int(x)-1] for x in vals.split(',')]
            print "Install Kubernetes on the following servers:"
            for s in k8servers:
                if type(s) is FabricComputeSlotEp:
                    print "\tChassis %s/%s type %s" % (s.chassis_id, s.rn, s.model)
                if type(s) is ComputeRackUnit:
                    print "\tServer %s type %s" % (s.rn, s.model)

            yn = raw_input("Is this correct? [N/y]: ")
            if yn == "y" or yn == "Y":
                return k8servers

def list_disks(handle, server):
    from ucsmsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk
    from ucsmsdk.mometa.storage.StorageController import StorageController
    from ucsmsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
    from ucsmsdk.mometa.fabric.FabricComputeSlotEp import FabricComputeSlotEp
    all_disks = []
    # get each controller of the server.
    if type(server) is FabricComputeSlotEp:
        cquery = '(dn, "sys/chassis-%s/blade-%s/board.*", type="re")' % (server.chassis_id, server.slot_id)
    else: 
        # don't do anything. 
        return all_disks
    controllers = handle.query_classid("StorageController", cquery)
    # get the disks of each controller. 
    for c in controllers:
        # get the disks: 
        # c.dn: sys/chassis-1/blade-8/board/storage-SAS-1
        dquery = '(dn, "%s", type="re")' % c.dn
        disks = handle.query_classid("StorageLocalDisk", dquery)
        for d in disks: 
            all_disks.append(d)
    return all_disks

# reset the disks of a specific server to unconfigured good so we can 
# use them!
def reset_disks(handle, server):
    from ucsmsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk
    disks = list_disks(handle, server)
    for d in disks:
	#print "changing disk: %s" % d.dn
        #print "disk state: %s" % d.disk_state
        #print "disk id: %s" % str(d.id)

        if d.disk_state == "jbod":
            print "setting to unconfigured good." 
 	    # get the first part of the dn which is the storage controller: 
            parent = "/".join(d.dn.split("/")[:-1])
            #print "parent is: %s" % parent
            mo = StorageLocalDisk(parent_mo_or_dn=parent, id=str(d.id),
               admin_action="unconfigured-good",
               admin_virtual_drive_id="unspecified",
               admin_action_trigger="triggered")
            handle.add_mo(mo, True)
            try:
               handle.commit()
            except UcsException as err:
               if err.error_code == "103":
                   print "\talready set to unconfigured-good."
               else: 
                   print "error code: %s" % err.error_code
                   print "error: %s" % err
    
    
def createKubeBootPolicy(handle, org):
    print "Creating Kube Boot Policy"
    from ucsmsdk.mometa.lsboot.LsbootPolicy import LsbootPolicy
    from ucsmsdk.mometa.lsboot.LsbootVirtualMedia import LsbootVirtualMedia
    from ucsmsdk.mometa.lsboot.LsbootStorage import LsbootStorage
    from ucsmsdk.mometa.lsboot.LsbootLocalStorage import LsbootLocalStorage
    from ucsmsdk.mometa.lsboot.LsbootDefaultLocalImage import LsbootDefaultLocalImage

    mo = LsbootPolicy(parent_mo_or_dn=org, name="kube", descr="Kuberenetes", reboot_on_update="yes", policy_owner="local", enforce_vnic_name="yes", boot_mode="legacy")
    mo_1 = LsbootVirtualMedia(parent_mo_or_dn=mo, access="read-only-remote-cimc", lun_id="0", order="2")
    mo_2 = LsbootStorage(parent_mo_or_dn=mo, order="1")
    mo_2_1 = LsbootLocalStorage(parent_mo_or_dn=mo_2, )
    mo_2_1_1 = LsbootDefaultLocalImage(parent_mo_or_dn=mo_2_1, order="1")

    handle.add_mo(mo, modify_present=True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"

def createBiosPolicy(handle, org):
    print "Creating Kube Bios policy"
    from ucsmsdk.mometa.bios.BiosVProfile import BiosVProfile
    from ucsmsdk.mometa.bios.BiosVfConsistentDeviceNameControl import BiosVfConsistentDeviceNameControl
    from ucsmsdk.mometa.bios.BiosVfFrontPanelLockout import BiosVfFrontPanelLockout
    from ucsmsdk.mometa.bios.BiosVfPOSTErrorPause import BiosVfPOSTErrorPause
    from ucsmsdk.mometa.bios.BiosVfQuietBoot import BiosVfQuietBoot
    from ucsmsdk.mometa.bios.BiosVfResumeOnACPowerLoss import BiosVfResumeOnACPowerLoss
    mo = BiosVProfile(parent_mo_or_dn=org, policy_owner="local", name="kube", descr="KUBaM Bios settings", reboot_on_update="yes")
    mo_1 = BiosVfConsistentDeviceNameControl(parent_mo_or_dn=mo, vp_cdn_control="enabled")
    mo_2 = BiosVfFrontPanelLockout(parent_mo_or_dn=mo, vp_front_panel_lockout="platform-default")
    mo_3 = BiosVfPOSTErrorPause(parent_mo_or_dn=mo, vp_post_error_pause="platform-default")
    mo_4 = BiosVfQuietBoot(parent_mo_or_dn=mo, vp_quiet_boot="platform-default")
    mo_5 = BiosVfResumeOnACPowerLoss(parent_mo_or_dn=mo, vp_resume_on_ac_power_loss="last-state")
    handle.add_mo(mo, modify_present=True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"

def deleteBiosPolicy(handle, org):
    print "Deleting Kubernetes Bios Policy"
    mo = handle.query_dn(org + "/bios-prof-kube")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"


def deleteKubeBootPolicy(handle, org):
    mo = handle.query_dn(org + "/boot-policy-kube")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"

def createKubeLocalDiskPolicy(handle, org):
    print "Creating Kube Local Disk Policy"
    from ucsmsdk.mometa.storage.StorageLocalDiskConfigPolicy import StorageLocalDiskConfigPolicy

    mo = StorageLocalDiskConfigPolicy(parent_mo_or_dn=org, protect_config="no", name="kube", descr="Kubernetes", flex_flash_raid_reporting_state="disable", flex_flash_state="disable", policy_owner="local", mode="raid-mirrored")
    handle.add_mo(mo)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"

def deleteKubeLocalDiskPolicy(handle, org):
    print "Deleting Kube Local Disk Policy"
    mo = handle.query_dn(org + "/local-disk-config-kube")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"

def createKubeUUIDPools(handle, org):
    print "Creating Kube UUID Pools"
    from ucsmsdk.mometa.uuidpool.UuidpoolPool import UuidpoolPool
    from ucsmsdk.mometa.uuidpool.UuidpoolBlock import UuidpoolBlock
    mo = UuidpoolPool(parent_mo_or_dn=org, policy_owner="local", prefix="derived", descr="Kubernetes Pool", assignment_order="default", name="kube")
    mo_1 = UuidpoolBlock(parent_mo_or_dn=mo, to="C888-888888888100", r_from="C888-888888888001")
    handle.add_mo(mo)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"

def deleteKubeUUIDPools(handle, org):
    print "Deleting Kube UUID Pool"
    mo = handle.query_dn(org + "/uuid-pool-kube")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"

def createKubeServerPool(handle, org):
    print "Creating Kubernetes Compute Pool"
    from ucsmsdk.mometa.compute.ComputePool import ComputePool
    mo = ComputePool(parent_mo_or_dn=org, policy_owner="local", name="Kubernetes", descr="")
    handle.add_mo(mo)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"

def addServersToKubePool(handle, servers, org):
    print "Adding servers to Kubernetes Pool"
    from ucsmsdk.mometa.compute.ComputePool import ComputePool
    from ucsmsdk.mometa.compute.ComputePooledSlot import ComputePooledSlot
    from ucsmsdk.mometa.compute.ComputePooledRackUnit import ComputePooledRackUnit
    from ucsmsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
    from ucsmsdk.mometa.fabric.FabricComputeSlotEp import FabricComputeSlotEp
    mo = ComputePool(parent_mo_or_dn=org, policy_owner="local", name="Kubernetes", descr="")
    for s in servers: 
        reset_disks(handle, s)
        if type(s) is FabricComputeSlotEp:
            ComputePooledSlot(parent_mo_or_dn=mo, slot_id=re.sub("slot-","", s.slot_id), chassis_id=str(s.chassis_id))
        if type(s) is ComputeRackUnit:
            ComputePooledRackUnit(parent_mo_or_dn=mo, id=re.sub("rack-unit-","", s.rn))
        handle.add_mo(mo, True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"


def deleteKubeServerPool(handle, org):
    print "Deleting Kubernetes Compute Pool"
    mo = handle.query_dn(org + "/compute-pool-Kubernetes")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"



def createServiceProfileTemplate(handle, org):
    print "Creating Kubernetes Service Profile Template"
    from ucsmsdk.mometa.ls.LsServer import LsServer
    from ucsmsdk.mometa.vnic.VnicConnDef import VnicConnDef
    from ucsmsdk.mometa.ls.LsRequirement import LsRequirement
    from ucsmsdk.mometa.lstorage.LstorageProfileBinding import LstorageProfileBinding
    mo = LsServer(parent_mo_or_dn=org, 
        policy_owner="local", 
        name="Kubernetes", 
        descr="Kubernetes Service Profile",
        type="updating-template",
        # Boot using Kubernetes Boot policy: local Disk, then Remote DVD
        boot_policy_name="kube",
        # Default Maintenance Policy
        maint_policy_name="default",
        # scrub policy
        scrub_policy_name="kube",
        # Bios Policy
        bios_profile_name="kube",
        # UUID Pool
        ident_pool_name="kube",
        # disks we use. 
        #local_disk_policy_name="kube",
        #storage_profile_name="kube",
        # virtual media policy
        vmedia_policy_name="kube"
        )
    # create vNIC Connection Policy
    VnicConnDef(parent_mo_or_dn=mo,
        lan_conn_policy_name="kube")
    # create server pool and add to template. 
    LsRequirement(parent_mo_or_dn=mo, name="Kubernetes")

    # add storage profile. 
    mo_1 = LstorageProfileBinding(parent_mo_or_dn=mo, storage_profile_name="kube")
    handle.add_mo(mo, True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"
    except Exception:
        print Exception



def deleteServiceProfileTemplate(handle, org):
    print "Deleting Kubernetes Service Profile Template"
    print "Deleting Kubernetes Compute Pool"
    mo = handle.query_dn(org + "/ls-Kubernetes")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"


def createServers(handle, servers, org):
    print "Creating Kubernetes Service Profiles"
    from ucsmsdk.ucsmethodfactory import ls_instantiate_n_named_template
    from ucsmsdk.ucsbasetype import DnSet, Dn

    for i, s in enumerate(servers):
        dn_set = DnSet()
        dn = Dn()
        sp_name = "kube0%d" % (i+1)
        dn.attr_set("value",sp_name)
        dn_set.child_add(dn)
        elem = ls_instantiate_n_named_template(cookie=handle.cookie, 
            dn=org + "/ls-Kubernetes", 
            in_error_on_existing="true", 
            in_name_set=dn_set,     
            in_target_org=org, 
            in_hierarchical="false")
        try:
            mo_list = handle.process_xml_elem(elem)
        except UcsException as err:
            if err.error_code == "105":
                print "\t" + sp_name + " already exists."
            else:
                print err

def deleteServers(handle, org):
    print "Deleting Kubernetes Nodes"

    filter_string = '(dn, "%s/ls-kube[0-9]+", type="re")' % org
    kube = handle.query_classid("lsServer", filter_string)
    for k in kube:
        print "Deleting " + k.name
        handle.remove_mo(k)
        try:
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            print "\t"+ k.name + ": " + err.error_descr

def createKubeVirtualMedia(handle, org):
    print "Adding Virtual Media Policy"
    from urlparse import urlparse
    import os.path
    yn = False
    url = ""
    while yn == False:
        print "What is the URL for the Boot ISO image?"
        url = raw_input("(E.g.: http://192.168.2.2/kubam/centos7.2-boot.iso) : ")
        print "You entered: " + url
        yn = raw_input("Is this correct? [y/N]: ")
        if yn != "y":
            yn = False
                
    o = urlparse(url)
    paths = os.path.split(o.path)
    scheme = o.scheme # http, https
    if scheme == "":
        scheme = "http"
    filename = paths[-1]
    address = o.hostname
    path =  "/".join(paths[:-1])
    name =  ".".join(paths[-1].split(".")[:-1]) 

    from ucsmsdk.mometa.cimcvmedia.CimcvmediaMountConfigPolicy import CimcvmediaMountConfigPolicy
    from ucsmsdk.mometa.cimcvmedia.CimcvmediaConfigMountEntry import CimcvmediaConfigMountEntry
    mo = CimcvmediaMountConfigPolicy(name="kube",
        retry_on_mount_fail="yes",
        parent_mo_or_dn=org, 
        policy_owner="local",
        descr="Kubernetes Boot Media")

    mo_1 = CimcvmediaConfigMountEntry(parent_mo_or_dn=mo,
        mapping_name=name,
        device_type="cdd",
        mount_protocol=scheme,
        remote_ip_address=address,
        image_name_variable="none",
        image_file_name=filename,
        image_path=path)

    mo_2 = CimcvmediaConfigMountEntry(parent_mo_or_dn=mo,
        mapping_name="kickstartImage",
        device_type="hdd",
        mount_protocol=scheme,
        remote_ip_address=address,
        image_name_variable="service-profile-name",
        image_path=path)
    handle.add_mo(mo, modify_present=True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"
    
def deleteVirtualMedia(handle, org):
    print "Deleting Kubernetes Virtual Media Policy"
    mo = handle.query_dn(org + "/mnt-cfg-policy-kube")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"


def createScrubPolicy(handle, org):
    from ucsmsdk.mometa.compute.ComputeScrubPolicy import ComputeScrubPolicy
    mo = ComputeScrubPolicy(flex_flash_scrub="no",
      parent_mo_or_dn=org, 
      name="kube",
      disk_scrub="yes",
      bios_settings_scrub="no",
      descr="Destroy data when SP is unassociated")
    handle.add_mo(mo, modify_present=True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"


def deleteScrubPolicy(handle, org):
    print "Deleting Kubernetes Scrub Policy"
    mo = handle.query_dn(org + "/scrub-kube")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"

def deleteDiskGroupConfig(handle, org):
    print "Deleting Disk Group config"
    mo = handle.query_dn(org + "/disk-group-config-Kube_Boot")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"

def deleteStorageProfile(handle, org):
    print "Deleting Storage Profile"
    mo = handle.query_dn(org + "/profile-kube")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"

def createDiskGroupConfig(handle, org):
    print "Adding Disk Group Config"
    from ucsmsdk.mometa.lstorage.LstorageDiskGroupConfigPolicy import LstorageDiskGroupConfigPolicy
    from ucsmsdk.mometa.lstorage.LstorageDiskGroupQualifier import LstorageDiskGroupQualifier
    from ucsmsdk.mometa.lstorage.LstorageVirtualDriveDef import LstorageVirtualDriveDef
    mo = LstorageDiskGroupConfigPolicy(parent_mo_or_dn=org, 
        policy_owner="local",
        name="kube_boot",
        descr="Kubernetes Boot Disk",
        raid_level="mirror")
    mo_1 = LstorageDiskGroupQualifier(parent_mo_or_dn=mo, 
        use_remaining_disks="no",
        num_ded_hot_spares="unspecified",
        drive_type="unspecified",
        num_drives="2",
        min_drive_size="unspecified",
        num_glob_hot_spares="unspecified")
    mo_2 = LstorageVirtualDriveDef(parent_mo_or_dn=mo, read_policy="platform-default",
        drive_cache="platform-default",
        strip_size="platform-default",
        io_policy="platform-default",
        write_cache_policy="platform-default",
        access_policy="platform-default")
    handle.add_mo(mo, modify_present=True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"

def createStorageProfile(handle, org):
    from ucsmsdk.mometa.lstorage.LstorageProfile import LstorageProfile 
    from ucsmsdk.mometa.lstorage.LstorageDasScsiLun import LstorageDasScsiLun
    mo = LstorageProfile(parent_mo_or_dn=org, 
        policy_owner="local",
        name="kube",
        descr="Kubernetes Storage Profile")
    mo_1 = LstorageDasScsiLun(parent_mo_or_dn=mo,
        local_disk_policy_name="kube_boot",
        auto_deploy="auto-deploy",
        expand_to_avail="yes",
        lun_map_type="non-shared",
        size="1",
        fractional_size="0",
        admin_state="online",
        deferred_naming="no",
        order="not-applicable",
        name="KubeLUN")
    handle.add_mo(mo, modify_present=True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"

def createKubeServers(handle, org):
    createKubeBootPolicy(handle, org)
    #createKubeLocalDiskPolicy(handle, org)
    createBiosPolicy(handle, org)
    createDiskGroupConfig(handle, org)
    createStorageProfile(handle, org)
    createScrubPolicy(handle, org)
    createKubeUUIDPools(handle, org)
    createKubeServerPool(handle, org)
    createKubeVirtualMedia(handle, org)
    servers = select_kube_servers(handle) 
    addServersToKubePool(handle, servers, org)
    createServiceProfileTemplate(handle, org)
    createServers(handle, servers, org)

def deleteKubeServers(handle, org):
    deleteServers(handle, org)
    deleteServiceProfileTemplate(handle, org)
    deleteKubeServerPool(handle, org)
    deleteVirtualMedia(handle, org)
    deleteScrubPolicy(handle, org)
    deleteKubeBootPolicy(handle, org)
    deleteStorageProfile(handle, org)
    deleteBiosPolicy(handle,org)
    deleteDiskGroupConfig(handle, org)
    #deleteKubeLocalDiskPolicy(handle, org)
    deleteKubeUUIDPools(handle, org)
    
