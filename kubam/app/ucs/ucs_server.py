from ucsmsdk.ucsexception import UcsException
from helper import KubamError



class UCSServer(object):
    # given an array and a string of numbers, make sure they are all in the array:
    @staticmethod
    def check_values(array, csv):
        indexes = csv.split(',')
        for i in indexes:
            try:
                i = int(i) - 1
            except Exception as e:
                print "bad value: " + i
                print e
                return False
            if i < 0 or i > len(array) - 1:
                return False
        return True
    @staticmethod
    def powerstat(handle):
        """
        Get's the power status of all nodes.
        """
        from ucsmsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
        from ucsmsdk.mometa.compute.ComputeBlade import ComputeBlade
        blades = handle.query_classid(class_id="ComputeBlade")
        servers = handle.query_classid(class_id="ComputeRackUnit")
        m = blades + servers
        all_servers = []
        for s in m:
            all_servers.append("{0}: {1}".format(s.dn, s.oper_power))
        return all_servers

    @staticmethod
    def power_server(handle, server, action):
        """
        Takes in a service profile and applies the appropriate power
        action to the service profile. The service profile should be
        the full organization of the server. e.g:
        "org-root/ls-miner04"
        """
        st = ""
        if action == "off":
            st = "admin-down"
        elif action == "on":
            st = "admin-up"
        elif action == "hardreset":
            st = "cycle-immediate"
        elif action == "softreset":
            st = "cycle-wait"
        else:
            raise KubamError("Power method {0} is not a valid power action.".format(action))


        if action in ["on", "off"] and server["service_profile"] == "":
            raise KubamError("Can not power {0}, no service profile associated with {1}".format(action, server["dn"]))
        from ucsmsdk.mometa.ls.LsPower import LsPower
        mo = LsPower(parent_mo_or_dn=server["service_profile"],
                     state=st)
        handle.add_mo(mo, True)
        try:
            handle.commit()
        except UcsException as err:
            raise KubamError("{0}".format(err))
    
    @staticmethod
    def list_servers(handle):
        from ucsmsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
        from ucsmsdk.mometa.compute.ComputeBlade import ComputeBlade

        blades = handle.query_classid(class_id="ComputeBlade")
        servers = handle.query_classid(class_id="ComputeRackUnit")
        m = blades + servers
        all_servers = []
        for i, s in enumerate(m):
            if type(s) is ComputeBlade:
                all_servers.append({
                    'type': "blade",
                    'label': s.usr_lbl,
                    'chassis_id': s.chassis_id,
                    'slot': s.rn.replace("blade-", ""),
                    'model': s.model,
                    'association': s.association,
                    'service_profile': s.assigned_to_dn,
                    'ram_speed': s.memory_speed,
                    'num_cpus': s.num_of_cpus,
                    'num_cores': s.num_of_cores,
                    'ram': s.total_memory,
                    'dn': s.dn,
                    'oper_power': s.oper_power
                })
            if type(s) is ComputeRackUnit:
                all_servers.append({
                    'type': "rack",
                    'label': s.usr_lbl,
                    'rack_id': s.rn.replace("rack-unit-", ""),
                    'model': s.model, 'association': s.association,
                    'service_profile': s.assigned_to_dn,
                    'ram_speed': s.memory_speed,
                    'num_cpus': s.num_of_cpus,
                    'num_cores': s.num_of_cores,
                    'ram': s.total_memory,
                    'dn': s.dn,
                    'oper_power': s.oper_power
                })
        return all_servers
   
    @staticmethod
    def list_blade(handle, server):
        chassis, slot = server.split("/")
        dn = "sys/chassis-{0}/blade-{1}".format(chassis, slot)
        server = handle.query_dn(dn)
        return server
    
    # Takes the server in standard Kubam mode which means it's just a hash, not a ComputeBlade object.
    @staticmethod
    def list_disks(handle, server):
        # Get each controller of the server.
        all_disks = []
        chassis, slot = server.server_id.split("/")
        cquery = "(dn, \"sys/chassis-{0}/blade-{1}/board.*\", type=\"re\")".format(chassis, slot)
        controllers = handle.query_classid("StorageController", cquery)
        # Get the disks of each controller.
        for c in controllers:
            # Get the disks: c.dn: sys/chassis-1/blade-8/board/storage-SAS-1
            dquery = "(dn, \"{0}\", type=\"re\")".format(c.dn)
            disks = handle.query_classid("StorageLocalDisk", dquery)
            for d in disks:
                all_disks.append(d)
        return all_disks

    # Reset the disks of a specific server to unconfigured good, so they can be used
    def reset_disks(self, handle, server):
        from ucsmsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk

        compute_blade = self.list_blade(handle, server)
        if compute_blade.oper_state != "unassociated":
            return
        disks = self.list_disks(handle, compute_blade)
        for d in disks:
            if d.disk_state == "jbod":
                print "setting to unconfigured good."
            # Get the first part of the dn which is the storage controller:
                parent = "/".join(d.dn.split("/")[:-1])

                mo = StorageLocalDisk(
                    parent_mo_or_dn=parent, id=str(d.id),
                    admin_action="unconfigured-good",
                    admin_virtual_drive_id="unspecified",  # Not available in 2.2(8g)
                    admin_action_trigger="triggered"
                )
                handle.add_mo(mo, True)
                try:
                    handle.commit()
                except UcsException as err:
                    if err.error_code == "103":
                        print "\talready set to unconfigured-good."
                    else:
                        print "error code: {0}".format(err.error_code)
                        print "error: {0}".format(err)
    
    @staticmethod
    def create_boot_policy(handle, org):
        from ucsmsdk.mometa.lsboot.LsbootPolicy import LsbootPolicy
        from ucsmsdk.mometa.lsboot.LsbootVirtualMedia import LsbootVirtualMedia
        from ucsmsdk.mometa.lsboot.LsbootStorage import LsbootStorage
        from ucsmsdk.mometa.lsboot.LsbootLocalStorage import LsbootLocalStorage
        from ucsmsdk.mometa.lsboot.LsbootDefaultLocalImage import LsbootDefaultLocalImage

        print "Creating KUBAM Boot Policy"
        mo_bp = LsbootPolicy(
            parent_mo_or_dn=org, name="kubam", descr="kubam", reboot_on_update="yes",
            policy_owner="local", enforce_vnic_name="yes", boot_mode="legacy"
        )
        LsbootVirtualMedia(parent_mo_or_dn=mo_bp, access="read-only-remote-cimc", lun_id="0", order="2")
        mo_bs = LsbootStorage(parent_mo_or_dn=mo_bp, order="1")
        mo_bls = LsbootLocalStorage(parent_mo_or_dn=mo_bs, )
        LsbootDefaultLocalImage(parent_mo_or_dn=mo_bls, order="1")

        handle.add_mo(mo_bp, modify_present=True)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        return 0, None

    @staticmethod
    def create_bios_policy(handle, org):
        from ucsmsdk.mometa.bios.BiosVProfile import BiosVProfile
        from ucsmsdk.mometa.bios.BiosVfConsistentDeviceNameControl import BiosVfConsistentDeviceNameControl
        from ucsmsdk.mometa.bios.BiosVfFrontPanelLockout import BiosVfFrontPanelLockout
        from ucsmsdk.mometa.bios.BiosVfPOSTErrorPause import BiosVfPOSTErrorPause
        from ucsmsdk.mometa.bios.BiosVfQuietBoot import BiosVfQuietBoot
        from ucsmsdk.mometa.bios.BiosVfResumeOnACPowerLoss import BiosVfResumeOnACPowerLoss

        print "Creating Kubam Bios policy"
        mo = BiosVProfile(
            parent_mo_or_dn=org, policy_owner="local", name="kubam",
            descr="KUBAM Bios settings", reboot_on_update="yes"
        )
        BiosVfConsistentDeviceNameControl(parent_mo_or_dn=mo, vp_cdn_control="enabled")
        BiosVfFrontPanelLockout(parent_mo_or_dn=mo, vp_front_panel_lockout="platform-default")
        BiosVfPOSTErrorPause(parent_mo_or_dn=mo, vp_post_error_pause="platform-default")
        BiosVfQuietBoot(parent_mo_or_dn=mo, vp_quiet_boot="platform-default")
        BiosVfResumeOnACPowerLoss(parent_mo_or_dn=mo, vp_resume_on_ac_power_loss="last-state")
        handle.add_mo(mo, modify_present=True)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        return 0, None

    @staticmethod
    def delete_bios_policy(handle, org):
        print "Deleting KUBAM Bios Policy"
        mo = handle.query_dn(org + "/bios-prof-kubam")
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    @staticmethod
    def delete_boot_policy(handle, org):
        mo = handle.query_dn(org + "/boot-policy-kubam")
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    @staticmethod
    def create_local_disk_policy(handle, org):
        from ucsmsdk.mometa.storage.StorageLocalDiskConfigPolicy import StorageLocalDiskConfigPolicy

        print "Creating KUBAM Local Disk Policy"
        mo = StorageLocalDiskConfigPolicy(
            parent_mo_or_dn=org, protect_config="no", name="kubam", descr="kubam",
            flex_flash_raid_reporting_state="disable", flex_flash_state="disable",
            policy_owner="local", mode="any-configuration"
        )
        handle.add_mo(mo)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        return 0, None

    @staticmethod
    def delete_local_disk_policy(handle, org):
        print "Deleting KUBAM Local Disk Policy"
        mo = handle.query_dn(org + "/local-disk-config-kubam")
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    @staticmethod
    def create_uuid_pools(handle, org):
        from ucsmsdk.mometa.uuidpool.UuidpoolPool import UuidpoolPool
        from ucsmsdk.mometa.uuidpool.UuidpoolBlock import UuidpoolBlock

        print "Creating UUID Pools"
        mo = UuidpoolPool(
            parent_mo_or_dn=org, policy_owner="local", prefix="derived",
            descr="KUBAM Pool", assignment_order="default", name="kubam"
        )
        UuidpoolBlock(parent_mo_or_dn=mo, to="C888-888888888100", r_from="C888-888888888001")
        handle.add_mo(mo)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        return 0, None

    @staticmethod
    def delete_uuid_pools(handle, org):
        mo = handle.query_dn(org + "/uuid-pool-kubam")

        print "Deleting KUBAM UUID Pool"
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    @staticmethod
    def create_server_pool(handle, org):
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
        return 0, None

    @staticmethod
    def add_servers_to_pool(handle, servers, org):
        from ucsmsdk.mometa.compute.ComputePool import ComputePool
        from ucsmsdk.mometa.compute.ComputePooledSlot import ComputePooledSlot
        from ucsmsdk.mometa.compute.ComputePooledRackUnit import ComputePooledRackUnit

        print "Adding servers to KUBAM Pool"
        mo = ComputePool(parent_mo_or_dn=org, policy_owner="local", name="kubam", descr="")
        handle.query_classid("computeBlade")
        if "blades" in servers:
            for s in servers["blades"]:
                # Don't reset disks, leave them the way they are.
                # reset_disks(handle, s)
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
        return 0, None

    @staticmethod
    def delete_server_pool(handle, org):
        print "Deleting KUBAM Compute Pool"
        mo = handle.query_dn(org + "/compute-pool-kubam")
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    @staticmethod
    def create_service_profile_template(handle, org):
        from ucsmsdk.mometa.ls.LsServer import LsServer
        from ucsmsdk.mometa.vnic.VnicConnDef import VnicConnDef
        from ucsmsdk.mometa.ls.LsRequirement import LsRequirement
        # from ucsmsdk.mometa.lstorage.LstorageProfileBinding import LstorageProfileBinding

        print "Creating KUBAM Service Profile Template"
        mo = LsServer(
            parent_mo_or_dn=org,
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

            # storage_profile_name="kubam",
            # virtual media policy
            vmedia_policy_name="kubam"
        )
        # Create vNIC Connection Policy
        VnicConnDef(parent_mo_or_dn=mo, lan_conn_policy_name="kubam")
        # Create server pool and add to template.
        LsRequirement(parent_mo_or_dn=mo, name="kubam")

        # Add storage profile.
        # LstorageProfileBinding(parent_mo_or_dn=mo, storage_profile_name="kubam")
        handle.add_mo(mo, True)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        except Exception as e:
            return 1, e
        return 0, None

    @staticmethod
    def delete_service_profile_template(handle, org):
        print "Deleting KUBAM Service Profile Template"
        mo = handle.query_dn(org + "/ls-KUBAM")
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    @staticmethod
    def check_org(template, org):
        """
        Make sure that the org in which we are creating the service prof
        has visibility to the actual org where the template is, other
        wise it won't be correct in UCS.
        In other words, the org should be at least the same or a suborg of
        the template.
        """
        # invalid would be: org: org-root, template: org-root/org-blah
        # valid would be: org: org-root/org-blah/org-blah1, template: org-root/org-blah
        import re
        tempOrg = re.sub('\/ls-.*', '', template)
        if org.startswith(tempOrg):
            return 0, None
        else:
            return 1, "template: {0} is not visible in org: {1}. Change the server group org to be a subset of the template org.".format(template, org)
    
    @staticmethod
    def create_server(handle, template, host_name, org):
        """
        Create a new service profile from a template that already exist.
        """

        err, msg = UCSServer.check_org(template, org)
        if err != 0:
            return 1, msg


        from ucsmsdk.ucsmethodfactory import ls_instantiate_n_named_template
        from ucsmsdk.ucsbasetype import DnSet, Dn
        dn_set = DnSet()
        dn = Dn()
        dn.attr_set("value", host_name)
        dn_set.child_add(dn)
        elem = ls_instantiate_n_named_template(
            cookie=handle.cookie, dn=template, in_error_on_existing="true", 
            in_name_set=dn_set, in_target_org=org, in_hierarchical="false"
        )

        try: 
            handle.process_xml_elem(elem)
        except UcsException as err:
            if err.error_code == "105":
                print "\tSP {0} already exists.".format(host_name)
            else:
                return 1, err.error_descr
        return 0, None
        
    @staticmethod
    def create_servers(handle, hosts, org):
        from ucsmsdk.ucsmethodfactory import ls_instantiate_n_named_template
        from ucsmsdk.ucsbasetype import DnSet, Dn

        print "Creating Service Profiles"
        for i, s in enumerate(hosts):
            err, msg = UCSServer.create_server(handle, "org-root/ls-KUBAM", s["name"], org)
            if err != 0:
                return err, msg
        return 0, None

    @staticmethod
    def delete_servers(handle, org, hostnames):
        print "Deleting KUBAM Nodes"
        for host in hostnames:
            filter_string = "(dn, \"{0}/ls-{1}\", type=\"re\")".format(org, host['name'])
            kube_host = handle.query_classid("lsServer", filter_string)
            if kube_host is None:
                continue
            for k in kube_host:
                print "Deleting " + k.name
                handle.remove_mo(k)
                try:
                    handle.commit()
                except AttributeError:
                    print "\talready deleted"
                except UcsException as err:
                    return 1, k.name + ": " + err.error_descr
        return 0, None

    @staticmethod
    def create_virtual_media(handle, org, kubam_ip, opersys):
        from ucsmsdk.mometa.cimcvmedia.CimcvmediaMountConfigPolicy import CimcvmediaMountConfigPolicy
        from ucsmsdk.mometa.cimcvmedia.CimcvmediaConfigMountEntry import CimcvmediaConfigMountEntry

        print "Adding Virtual Media Policy"
        from urlparse import urlparse
        import os.path
        url = "http://" + kubam_ip + "/kubam/" + opersys + "-boot.iso"
        if opersys.startswith("win"):
            url = "http://" + kubam_ip + "/kubam/" + "KUBAM_WinPE.iso"
        
        o = urlparse(url)
        paths = os.path.split(o.path)
        scheme = o.scheme  # HTTP, HTTPS
        if scheme == "":
            scheme = "http"
        filename = paths[-1]
        address = o.hostname
        path = "/".join(paths[:-1])
        name = ".".join(paths[-1].split(".")[:-1])

        mo = CimcvmediaMountConfigPolicy(
            name="KUBAM_" + opersys ,
            retry_on_mount_fail="yes",
            parent_mo_or_dn=org,
            policy_owner="local",
            descr="KUBAM vmedia policy for " + opersys
        )

        CimcvmediaConfigMountEntry(
            parent_mo_or_dn=mo,
            mapping_name=name,
            device_type="cdd",
            mount_protocol=scheme,
            remote_ip_address=address,
            image_name_variable="none",
            image_file_name=filename,
            image_path=path
        )

        CimcvmediaConfigMountEntry(
            parent_mo_or_dn=mo,
            mapping_name="ServerImage",
            device_type="hdd",
            mount_protocol=scheme,
            remote_ip_address=address,
            image_name_variable="service-profile-name",
            image_path=path
        )

        handle.add_mo(mo, modify_present=True)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        return 0, None

    @staticmethod
    def delete_virtual_media(handle, org):
        print "Deleting KUBAM Virtual Media Policy"
        mo = handle.query_dn(org + "/mnt-cfg-policy-kubam")
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    @staticmethod
    def create_scrub_policy(handle, org):
        from ucsmsdk.mometa.compute.ComputeScrubPolicy import ComputeScrubPolicy

        mo = ComputeScrubPolicy(
            flex_flash_scrub="no", parent_mo_or_dn=org, name="kubam",
            disk_scrub="yes", bios_settings_scrub="no", descr="Destroy data when SP is unassociated"
        )
        handle.add_mo(mo, modify_present=True)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        return 0, None



    @staticmethod
    def associate_server(handle, org, h):
        """
        handle: connection to ucsc
        org: org-root or something else
        h: this is the hash of the host.
        - 'server' is the server to be bound to.
        - the service profile is the name of the host with the org:
        - eg: <org>/ls-<h[name]> => org-root/ls-server
        - the blade will be something like:
        - 1006/1/6 or 1
        """

        # translate physical server name:
        server = h['server']
        try:
            chassis, slot = server.split("/")
        except Exception as e:
            return 1, "server value should be <chassis ID>/<serverID>.  Not {0}".format(server)

        #dn = "compute/sys-1009/chassis-{0}/blade-{1}"
        dn = "sys/chassis-{0}/blade-{1}".format(chassis, slot)

        sp = "{0}/ls-{1}".format(org, h['name'])
        #TODO more error checking.

        from ucsmsdk.mometa.ls.LsBinding import LsBinding
        mo = LsBinding(parent_mo_or_dn=sp,
            #pn_dn="sys/chassis-1/blade-6",
            pn_dn=dn,
            restrict_migration="no")
        handle.add_mo(mo, True)
        try:
            handle.commit()
        except AttributeError:
            print "\talready associated"
        except UcsException as err:
                return 1, sp_name + ": " + err.error_descr
        return 0, None

    @staticmethod
    def delete_scrub_policy(handle, org):
        print "Deleting KUBAM Scrub Policy"
        mo = handle.query_dn(org + "/scrub-kubam")
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    @staticmethod
    def create_disk_group_config(handle, org):
        from ucsmsdk.mometa.lstorage.LstorageDiskGroupConfigPolicy import LstorageDiskGroupConfigPolicy
        from ucsmsdk.mometa.lstorage.LstorageDiskGroupQualifier import LstorageDiskGroupQualifier
        from ucsmsdk.mometa.lstorage.LstorageVirtualDriveDef import LstorageVirtualDriveDef

        print "Adding Disk Group Config"
        mo = LstorageDiskGroupConfigPolicy(
            parent_mo_or_dn=org,
            policy_owner="local",
            name="kubam_boot",
            descr="KUBAM Boot Disk",
            raid_level="mirror"
        )
        LstorageDiskGroupQualifier(
            parent_mo_or_dn=mo, use_remaining_disks="no", num_ded_hot_spares="unspecified",
            drive_type="unspecified", num_drives="2", min_drive_size="unspecified",
            num_glob_hot_spares="unspecified"
        )
        LstorageVirtualDriveDef(
            parent_mo_or_dn=mo, read_policy="platform-default", drive_cache="platform-default",
            strip_size="platform-default", io_policy="platform-default",
            write_cache_policy="platform-default", access_policy="platform-default"
        )
        handle.add_mo(mo, modify_present=True)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        return 0, None

    @staticmethod
    def delete_disk_group_config(handle, org):
        print "Deleting Disk Group config"
        mo = handle.query_dn(org + "/disk-group-config-kubam_boot")
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    @staticmethod
    def create_storage_profile(handle, org):
        from ucsmsdk.mometa.lstorage.LstorageProfile import LstorageProfile
        from ucsmsdk.mometa.lstorage.LstorageDasScsiLun import LstorageDasScsiLun

        mo = LstorageProfile(
            parent_mo_or_dn=org,
            policy_owner="local",
            name="kubam",
            descr="KUBAM Storage Profile"
        )
        LstorageDasScsiLun(
            parent_mo_or_dn=mo,
            local_disk_policy_name="kubam_boot",
            auto_deploy="auto-deploy",
            expand_to_avail="yes",
            lun_map_type="non-shared",  # Not available in 2.2(8g)
            size="1",
            fractional_size="0",
            admin_state="online",
            deferred_naming="no",  # Not available in 2.2(8g)
            order="not-applicable",  # Not available in 2.2(8g)
            name="KubeLUN"
        )
        handle.add_mo(mo, modify_present=True)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        return 0, None

    @staticmethod
    def delete_storage_profile(handle, org):
        print "Deleting Storage Profile"
        mo = handle.query_dn(org + "/profile-kubam")
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcsException as err:
            return 1, err.error_descr
        return 0, None

    def create_server_resources(self, handle, org, hosts, servers, kubam_ip):
        err, msg = self.create_boot_policy(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.create_bios_policy(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.create_local_disk_policy(handle, org)
        if err != 0:
            return err, msg

        # err, msg = self.create_disk_group_config(handle, org)
        # if err != 0:
        #    return err, msg

        # err, msg = self.create_storage_profile(handle, org)
        # if err != 0:
        #    return err, msg

        err, msg = self.create_scrub_policy(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.create_uuid_pools(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.create_server_pool(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.create_virtual_media(handle, org, kubam_ip, hosts)
        if err != 0:
            return err, msg

        err, msg = self.add_servers_to_pool(handle, servers, org)
        if err != 0:
            return err, msg

        err, msg = self.create_service_profile_template(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.create_servers(handle, hosts, org)
        return err, msg

    def delete_server_resources(self, handle, org, hosts):
        err, msg = self.delete_servers(handle, org, hosts)
        if err != 0:
            return err, msg

        err, msg = self.delete_service_profile_template(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.delete_server_pool(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.delete_virtual_media(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.delete_scrub_policy(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.delete_boot_policy(handle, org)
        if err != 0:
            return err, msg

        # err, msg = self.delete_storage_profile(handle, org)
        # if err != 0:
        #    return err, msg

        err, msg = self.delete_bios_policy(handle, org)
        if err != 0:
            return err, msg

        # err, msg = self.delete_disk_group_config(handle, org)
        # if err != 0:
        #    return err, msg

        err, msg = self.delete_local_disk_policy(handle, org)
        if err != 0:
            return err, msg

        err, msg = self.delete_uuid_pools(handle, org)
        if err != 0:
            return err, msg
        return err, msg

    @staticmethod
    def make_profile_from_template(handle, org, host):
        template = host['service_profile_template']
        name = host['name']
        err, msg = UCSServer.create_server(handle, template, name, org)
        return err, msg

    @staticmethod
    def make_vmedias(handle, org, kubam_ip, oses):
        for os in oses:
            err, msg = UCSServer.create_virtual_media(handle, org, kubam_ip, os)
            if err != 0:
                return err, msg
        return 0, ""
