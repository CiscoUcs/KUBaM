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

def list_servers(handle):
    from ucsmsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
    from ucsmsdk.mometa.compute.ComputeBlade import ComputeBlade
    blades = handle.query_classid(class_id="ComputeBlade") 
    servers = handle.query_classid(class_id="ComputeRackUnit") 
    m = blades + servers
    all_servers = []
    for i, s in enumerate(m):
        if type(s) is ComputeBlade:
            all_servers.append({"type":"blade", "label": s.usr_lbl, "chassis_id": s.chassis_id, "slot": s.rn.replace('blade-', ''), "model": s.model, "association" : s.association, "service_profile" : s.assigned_to_dn })
        if type(s) is ComputeRackUnit:
            all_servers.append({"type":"rack", "label": s.usr_lbl, "rack_id": s.rn.replace('rack-unit-', ''), "model": s.model, "association": s.association, "service_profile": s.assigned_to_dn  })
    return all_servers
   
 
def list_blade(handle, server):
    from ucsmsdk.mometa.compute.ComputeBlade import ComputeBlade
    chassis, slot = server.split("/")
    dn = "sys/chassis-%s/blade-%s" % (chassis,slot)
    server = handle.query_dn(dn)
    return server
    
# takes the server in standard kubam mode which means its just a hash, not a ComputeBlade object. 
def list_disks(handle, server):
    from ucsmsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk
    from ucsmsdk.mometa.storage.StorageController import StorageController
    from ucsmsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
    from ucsmsdk.mometa.compute.ComputeBlade import ComputeBlade
    from ucsmsdk.mometa.fabric.FabricComputeSlotEp import FabricComputeSlotEp
    # get each controller of the server.
    all_disks = []
    chassis, slot = server.server_id.split("/")
    cquery = '(dn, "sys/chassis-%s/blade-%s/board.*", type="re")' % (chassis, slot)
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
    from ucsmsdk.mometa.compute.ComputeBlade import ComputeBlade
    
    compute_blade = list_blade(handle, server)
    if compute_blade.oper_state != "unassociated":
        return
    disks = list_disks(handle, compute_blade)
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
               admin_virtual_drive_id="unspecified", # not in 2.2(8g)
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
    
    
def createBootPolicy(handle, org):
    print "Creating KUBAM Boot Policy"
    from ucsmsdk.mometa.lsboot.LsbootPolicy import LsbootPolicy
    from ucsmsdk.mometa.lsboot.LsbootVirtualMedia import LsbootVirtualMedia
    from ucsmsdk.mometa.lsboot.LsbootStorage import LsbootStorage
    from ucsmsdk.mometa.lsboot.LsbootLocalStorage import LsbootLocalStorage
    from ucsmsdk.mometa.lsboot.LsbootDefaultLocalImage import LsbootDefaultLocalImage

    mo = LsbootPolicy(parent_mo_or_dn=org, name="kubam", descr="kubam", reboot_on_update="yes", policy_owner="local", enforce_vnic_name="yes", boot_mode="legacy")
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
        else:
            return 1, err.error_descr
    return 0, ""

def createBiosPolicy(handle, org):
    print "Creating Kubam Bios policy"
    from ucsmsdk.mometa.bios.BiosVProfile import BiosVProfile
    from ucsmsdk.mometa.bios.BiosVfConsistentDeviceNameControl import BiosVfConsistentDeviceNameControl
    from ucsmsdk.mometa.bios.BiosVfFrontPanelLockout import BiosVfFrontPanelLockout
    from ucsmsdk.mometa.bios.BiosVfPOSTErrorPause import BiosVfPOSTErrorPause
    from ucsmsdk.mometa.bios.BiosVfQuietBoot import BiosVfQuietBoot
    from ucsmsdk.mometa.bios.BiosVfResumeOnACPowerLoss import BiosVfResumeOnACPowerLoss
    mo = BiosVProfile(parent_mo_or_dn=org, policy_owner="local", name="kubam", descr="KUBAM Bios settings", reboot_on_update="yes")
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
        else:
            return 1, err.error_descr
    return 0, ""

def deleteBiosPolicy(handle, org):
    print "Deleting KUBAM Bios Policy"
    mo = handle.query_dn(org + "/bios-prof-kubam")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""


def deleteBootPolicy(handle, org):
    mo = handle.query_dn(org + "/boot-policy-kubam")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""

def createLocalDiskPolicy(handle, org):
    print "Creating KUBAM Local Disk Policy"
    from ucsmsdk.mometa.storage.StorageLocalDiskConfigPolicy import StorageLocalDiskConfigPolicy

    #mo = StorageLocalDiskConfigPolicy(parent_mo_or_dn=org, protect_config="no", name="kube", descr="kubam", flex_flash_raid_reporting_state="disable", flex_flash_state="disable", policy_owner="local", mode="raid-mirrored")
    mo = StorageLocalDiskConfigPolicy(parent_mo_or_dn=org, protect_config="no", name="kubam", descr="kubam", flex_flash_raid_reporting_state="disable", flex_flash_state="disable", policy_owner="local", mode="any-configuration")
    handle.add_mo(mo)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"
        else:
            return 1, err.error_descr
    return 0, ""

def deleteLocalDiskPolicy(handle, org):
    print "Deleting KUBAM Local Disk Policy"
    mo = handle.query_dn(org + "/local-disk-config-kubam")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""

def createUUIDPools(handle, org):
    print "Creating UUID Pools"
    from ucsmsdk.mometa.uuidpool.UuidpoolPool import UuidpoolPool
    from ucsmsdk.mometa.uuidpool.UuidpoolBlock import UuidpoolBlock
    mo = UuidpoolPool(parent_mo_or_dn=org, policy_owner="local", prefix="derived", descr="KUBAM Pool", assignment_order="default", name="kubam")
    mo_1 = UuidpoolBlock(parent_mo_or_dn=mo, to="C888-888888888100", r_from="C888-888888888001")
    handle.add_mo(mo)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"
        else:
            return 1, err.error_descr
    return 0, ""

def deleteUUIDPools(handle, org):
    print "Deleting KUBAM UUID Pool"
    mo = handle.query_dn(org + "/uuid-pool-kubam")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""

def createServerPool(handle, org):
    print "Creating KUBAM Compute Pool"
    from ucsmsdk.mometa.compute.ComputePool import ComputePool
    mo = ComputePool(parent_mo_or_dn=org, policy_owner="local", name="kubam", descr="")
    handle.add_mo(mo)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"
        else:
            return 1, err.error_descr
    return 0, ""

def addServersToPool(handle, servers, org):
    print "Adding servers to KUBAM Pool"
    from ucsmsdk.mometa.compute.ComputePool import ComputePool
    from ucsmsdk.mometa.compute.ComputePooledSlot import ComputePooledSlot
    from ucsmsdk.mometa.compute.ComputePooledRackUnit import ComputePooledRackUnit
    mo = ComputePool(parent_mo_or_dn=org, policy_owner="local", name="kubam", descr="")
    blades = handle.query_classid("computeBlade")
    if "blades" in servers:
        for s in servers["blades"]:
            # Don't reset disks, leave them the way they are. 
            #reset_disks(handle, s)
            chassis, slot = s.split("/")
            ComputePooledSlot(parent_mo_or_dn=mo, slot_id=str(slot), chassis_id=str(chassis))
    if "rack_servers" in servers:
        for r in servers["rack_servers"]:
            ComputePooledRackUnit(parent_mo_or_dn=mo, id=r)
    handle.add_mo(mo, True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"
        else:
            return 1, err.error_descr
    return 0, ""


def deleteServerPool(handle, org):
    print "Deleting KUBAM Compute Pool"
    mo = handle.query_dn(org + "/compute-pool-kubam")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""



def createServiceProfileTemplate(handle, org):
    print "Creating KUBAM Service Profile Template"
    from ucsmsdk.mometa.ls.LsServer import LsServer
    from ucsmsdk.mometa.vnic.VnicConnDef import VnicConnDef
    from ucsmsdk.mometa.ls.LsRequirement import LsRequirement
    from ucsmsdk.mometa.lstorage.LstorageProfileBinding import LstorageProfileBinding
    mo = LsServer(parent_mo_or_dn=org, 
        policy_owner="local", 
        name="KUBAM", 
        descr="KUBAM Service Profile Template",
        type="updating-template",
        # Boot using Kubernetes Boot policy: local Disk, then Remote DVD
        boot_policy_name="kubam",
        # Default Maintenance Policy
        maint_policy_name="default",
        # scrub policy
        scrub_policy_name="kubam",
        # Bios Policy
        bios_profile_name="kubam",
        # UUID Pool
        ident_pool_name="kubam",
        # disks we use. 
        local_disk_policy_name="kubam",

        #storage_profile_name="kubam",
        # virtual media policy
        vmedia_policy_name="kubam"
        )
    # create vNIC Connection Policy
    VnicConnDef(parent_mo_or_dn=mo,
        lan_conn_policy_name="kubam")
    # create server pool and add to template. 
    LsRequirement(parent_mo_or_dn=mo, name="kubam")

    # add storage profile. 
    #mo_1 = LstorageProfileBinding(parent_mo_or_dn=mo, storage_profile_name="kubam")
    handle.add_mo(mo, True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"
        else:
            return 1, err.error_descr
    except Exception:
        return 1, "%s" % Exception
    return 0, ""



def deleteServiceProfileTemplate(handle, org):
    print "Deleting KUBAM Service Profile Template"
    mo = handle.query_dn(org + "/ls-KUBAM")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""


def createServers(handle, hosts, org):
    print "Creating Service Profiles"
    from ucsmsdk.ucsmethodfactory import ls_instantiate_n_named_template
    from ucsmsdk.ucsbasetype import DnSet, Dn

    for i, s in enumerate(hosts):
        dn_set = DnSet()
        dn = Dn()
        sp_name = s["name"]
        dn.attr_set("value",sp_name)
        dn_set.child_add(dn)
        elem = ls_instantiate_n_named_template(cookie=handle.cookie, 
            dn=org + "/ls-KUBAM", 
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
                return 1, err.error_descr
    return 0, ""

def deleteServers(handle, org, hostnames):
    print "Deleting KUBAM Nodes"
    for host in hostnames: 
        #filter_string = '(dn, "%s/ls-kube[0-9]+", type="re")' % org
        filter_string = '(dn, "%s/ls-%s", type="re")' % (org, host["name"]) 
        kube_host = handle.query_classid("lsServer", filter_string)
        if kube_host is None:
            next
        for k in kube_host: 
            print "Deleting " + k.name
            handle.remove_mo(k)
            try:
                handle.commit()
            except AttributeError:
                print "\talready deleted"
            except UcsException as err:
                return 1, k.name + ": " + err.error_descr
    return 0, ""

def createVirtualMedia(handle, org, kubam_ip, hosts):
    print "Adding Virtual Media Policy"
    from urlparse import urlparse
    import os.path
    yn = False
    url = "http://" + kubam_ip + "/kubam/" + hosts[0]["os"] + "-boot.iso"            
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
    mo = CimcvmediaMountConfigPolicy(name="kubam",
        retry_on_mount_fail="yes",
        parent_mo_or_dn=org, 
        policy_owner="local",
        descr="KUBAM Boot Media")

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
        else:
            return 1, err.error_descr
    return 0, ""
    
def deleteVirtualMedia(handle, org):
    print "Deleting KUBAM Virtual Media Policy"
    mo = handle.query_dn(org + "/mnt-cfg-policy-kubam")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""


def createScrubPolicy(handle, org):
    from ucsmsdk.mometa.compute.ComputeScrubPolicy import ComputeScrubPolicy
    mo = ComputeScrubPolicy(flex_flash_scrub="no",
      parent_mo_or_dn=org, 
      name="kubam",
      disk_scrub="yes",
      bios_settings_scrub="no",
      descr="Destroy data when SP is unassociated")
    handle.add_mo(mo, modify_present=True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"
        else:
            return 1, err.error_descr
    return 0, ""


def deleteScrubPolicy(handle, org):
    print "Deleting KUBAM Scrub Policy"
    mo = handle.query_dn(org + "/scrub-kubam")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""

def deleteDiskGroupConfig(handle, org):
    print "Deleting Disk Group config"
    mo = handle.query_dn(org + "/disk-group-config-kubam_boot")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""

def deleteStorageProfile(handle, org):
    print "Deleting Storage Profile"
    mo = handle.query_dn(org + "/profile-kubam")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""

def createDiskGroupConfig(handle, org):
    print "Adding Disk Group Config"
    from ucsmsdk.mometa.lstorage.LstorageDiskGroupConfigPolicy import LstorageDiskGroupConfigPolicy
    from ucsmsdk.mometa.lstorage.LstorageDiskGroupQualifier import LstorageDiskGroupQualifier
    from ucsmsdk.mometa.lstorage.LstorageVirtualDriveDef import LstorageVirtualDriveDef
    mo = LstorageDiskGroupConfigPolicy(parent_mo_or_dn=org, 
        policy_owner="local",
        name="kubam_boot",
        descr="KUBAM Boot Disk",
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
        else:
            return 1, err.error_descr
    return 0, ""

def createStorageProfile(handle, org):
    from ucsmsdk.mometa.lstorage.LstorageProfile import LstorageProfile 
    from ucsmsdk.mometa.lstorage.LstorageDasScsiLun import LstorageDasScsiLun
    mo = LstorageProfile(parent_mo_or_dn=org, 
        policy_owner="local",
        name="kubam",
        descr="KUBAM Storage Profile")
    mo_1 = LstorageDasScsiLun(parent_mo_or_dn=mo,
        local_disk_policy_name="kubam_boot",
        auto_deploy="auto-deploy",
        expand_to_avail="yes",
        lun_map_type="non-shared", # this is not available in 2.2(8g)
        size="1",
        fractional_size="0",
        admin_state="online",
        deferred_naming="no", # this is not available in 2.2(8g)
        order="not-applicable", # not available in 2.2(8g)
        name="KubeLUN")
    handle.add_mo(mo, modify_present=True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\talready exists"
        else:
            return 1, err.error_descr
    return 0, ""

def createServerResources(handle, org, hosts, servers, kubam_ip):
    err, msg = createBootPolicy(handle, org)
    if err != 0:
        return err, msg

    err, msg = createBiosPolicy(handle, org)
    if err != 0:
        return err, msg

    err, msg = createLocalDiskPolicy(handle, org)
    if err != 0:
        return err, msg

    #err, msg = createDiskGroupConfig(handle, org)
    #if err != 0:
    #    return err, msg

    #err, msg = createStorageProfile(handle, org)
    #if err != 0:
    #    return err, msg

    err, msg = createScrubPolicy(handle, org)
    if err != 0:
        return err, msg

    err, msg = createUUIDPools(handle, org)
    if err != 0:
        return err, msg

    err, msg = createServerPool(handle, org)
    if err != 0:
        return err, msg

    err, msg = createVirtualMedia(handle, org, kubam_ip, hosts)
    if err != 0:
        return err, msg

    err, msg = addServersToPool(handle, servers, org)
    if err != 0:
        return err, msg

    err, msg = createServiceProfileTemplate(handle, org)
    if err != 0:
        return err, msg

    err, msg = createServers(handle, hosts, org)
    return err, msg

def deleteServerResources(handle, org, hosts):
    err, msg = deleteServers(handle, org, hosts)
    if err != 0:
        return err, msg
    err, msg = deleteServiceProfileTemplate(handle, org)
    if err != 0:
        return err, msg
    err, msg = deleteServerPool(handle, org)
    if err != 0:
        return err, msg
    err, msg = deleteVirtualMedia(handle, org)
    if err != 0:
        return err, msg
    err, msg = deleteScrubPolicy(handle, org)
    if err != 0:
        return err, msg
    err, msg = deleteBootPolicy(handle, org)
    if err != 0:
        return err, msg
    #err, msg = deleteStorageProfile(handle, org)
    #if err != 0:
    #    return err, msg
    err, msg = deleteBiosPolicy(handle,org)
    if err != 0:
        return err, msg
    #err, msg = deleteDiskGroupConfig(handle, org)
    #if err != 0:
    #    return err, msg
    err, msg = deleteLocalDiskPolicy(handle, org)
    if err != 0:
        return err, msg

    err, msg = deleteUUIDPools(handle, org)
    if err != 0:
        return err, msg
    return err, msg
    
