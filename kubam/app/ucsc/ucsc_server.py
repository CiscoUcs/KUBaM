from helper import KubamError
from ucscsdk.ucscexception import UcscException
import re

class UCSCServer(object):

    @staticmethod
    def power_server(handle, server, action):
        """
        Takes in a server object and applies the appropriate power
        action to the server
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
        from ucscsdk.mometa.ls.LsServerOperation import LsServerOperation
        # UCS central requires a few different ways of doing remote calls to the server.  
        # an example looks as follows:
        #  mo = LsServerOperation(parent_mo_or_dn="org-root/org-SLCLAB3/req-SLC-KVM-02/inst-1009",
        #                state="admin-up") 
        # notice the 'ls-' is changed to 'req-' and the domain ID is appended to the end. 
        # also instaed of handle.add_mo set_mo seems to be the way to make this work.
        mo_name = "{0}/inst-{1}".format(server["service_profile"], server['domain_id'])
        mo_name = mo_name.replace("/ls-", "/req-")
        mo = LsServerOperation(parent_mo_or_dn=mo_name,  state=st)
        handle.add_mo(mo, True)
        try:
            handle.commit()
        except UcscException as err:
            raise KubamError("{0}\n{1}".format(mo, err))        


    @staticmethod
    def list_servers(handle):
        from ucscsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
        from ucscsdk.mometa.compute.ComputeBlade import ComputeBlade

        blades = handle.query_classid(class_id="ComputeBlade")
        servers = handle.query_classid(class_id="ComputeRackUnit")
        m = blades + servers
        all_servers = []
        for i, s in enumerate(m):
            if type(s) is ComputeBlade:
                all_servers.append({
                    'type': "blade",
                    'label': s.usr_lbl,
                    'ram': s.total_memory,
                    'domain_id': re.search('.*sys-(.+?)/.*', s.dn).group(1),
                    'ram_speed': s.memory_speed,
                    'num_cpus': s.num_of_cpus,
                    'num_cores': s.num_of_cores,
                    'chassis_id': s.chassis_id,
                    'slot': s.rn.replace("blade-", ""),
                    'model': s.model,
                    'association': s.association,
                    'service_profile': s.assigned_to_dn,
                    'dn': s.dn,
                    'oper_power': s.oper_power
                })
            if type(s) is ComputeRackUnit:
                all_servers.append({
                    'type': "rack",
                    'label': s.usr_lbl,
                    'ram': s.total_memory,
                    'domain_id': re.search('.*sys-(.+?)/.*', s.dn).group(1),
                    'ram_speed': s.memory_speed,
                    'num_cpus': s.num_of_cpus,
                    'num_cores': s.num_of_cores,
                    'rack_id': s.rn.replace("rack-unit-", ""),
                    'model': s.model, 'association': s.association,
                    'service_profile': s.assigned_to_dn,
                    'dn': s.dn,
                    'oper_power': s.oper_power
                })
        return all_servers
    
    @staticmethod
    def list_templates(handle):

        filter_str = "(type, 'initial-template', type='eq') or (type, 'updating-template', type='eq')"
        try:
            query = handle.query_classid("lsServer", filter_str=filter_str)
            templates = list()

            for q in query:
                templates.append({"name": q.name})
            return templates

        except UcscException as e:
            raise KubamError(e)

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
        - 1/6 or 1
        """

        # translate physical server name: 
        server = h['server']
        try:
            domain, chassis, slot = server.split("/")
        except Exception as e:
            return 1, "server value should be <domain ID>/<chassis ID>/<server ID>.  Not {0}".format(server)

        #dn = "compute/sys-1009/chassis-{0}/blade-{1}"
        dn = "compute/sys-{0}/chassis-{1}/blade-{2}".format(domain, chassis, slot)
        
        sp = "{0}/ls-{1}".format(org, h['name'])
        #TODO more error checking. 
        
        from ucscsdk.mometa.ls.LsBinding import LsBinding
        mo = LsBinding(parent_mo_or_dn=sp,
            #pn_dn="sys/chassis-1/blade-6",
            pn_dn=dn,
            restrict_migration="no")
        handle.add_mo(mo, True)
        try:
            handle.commit()
        except AttributeError:
            print "\talready associated."
        except UcscException as err:
                return 1, sp_name + ": " + err.error_descr
        return 0, None

    @staticmethod
    def disassociate_server(handle, sp):
        #mo = handle.query_dn("org-root/ls-miner06/pn-req")
        mo = handle.query_dn(sp)
        handle.remove_mo(mo)
        try:
            handle.commit()
        except UcscException as err:
                return 1, sp_name + ": " + err.error_descr
        

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
    def create_server(handle, template, name, org):
        """
        Create a new service profile from a template that already exist.
        Must use the dn for the template: org-root/ls-TestTemplate
        """
        err, msg = UCSCServer.check_org(template, org)
        if err != 0:
            return 1, msg

        from ucscsdk.ucscmethodfactory import ls_instantiate_n_named_template
        from ucscsdk.ucscbasetype import DnSet, Dn
        dn_set = DnSet()
        dn = Dn()
        dn.attr_set("value", name)
        dn_set.child_add(dn)
        elem = ls_instantiate_n_named_template(
            cookie=handle.cookie, 
            dn=template, 
            in_error_on_existing="true",
            in_name_set=dn_set, 
            in_target_org=org, 
            in_pool_name="",
            in_qualifier_name = "",
            in_hierarchical="false"
        )

        try:
            handle.process_xml_elem(elem)
        except UcscException as err:
            if err.error_code == "105":
                print "\tSP {0} already exists.".format(name)
            else:
                return 1, err.error_descr
        return 0, None
    
    @staticmethod
    def delete_server(handle, sp_name, org):
        """
        Delete a service profile template
        delete_server(h, "test1", "org-root")
        """
        filter_string = "(dn, \"{0}/ls-{1}\", type=\"re\")".format(org, sp_name)
        sp = handle.query_classid("lsServer", filter_string)
        if sp is None:
            return 1, "Service Profile: {0} is not created.".format(sp_name)
        #print "Deleting " + sp_name
        if len(sp) < 1:
            return 1, "Service Profile: {0} is not created.".format(sp_name)
        handle.remove_mo(sp[0])
        try:
            handle.commit()
        except AttributeError:
            print "\talready deleted"
        except UcscException as err:
                return 1, sp_name + ": " + err.error_descr
        return 0, None

    @staticmethod
    def create_virtual_media(handle, org, kubam_ip, os):
        #TODO
        pass

    @staticmethod
    def make_profile_from_template(handle, org, host):
        if not isinstance(host, dict):
            return 1, "hosts argument not valid"
        template = host['service_profile_template']
        name = host['name']
        err, msg = UCSCServer.create_server(handle, template, name, org)
        return err, msg

    @staticmethod
    def create_virtual_media(handle, org, kubam_ip, opersys):
        from ucscsdk.mometa.cimcvmedia.CimcvmediaMountConfigPolicy import CimcvmediaMountConfigPolicy
        from ucscsdk.mometa.cimcvmedia.CimcvmediaConfigMountEntry import CimcvmediaConfigMountEntry

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
            #policy_owner="local",
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
        except UcscException as err:
            if err.error_code == "103":
                print "\talready exists"
            else:
                return 1, err.error_descr
        return 0, None

    @staticmethod
    def make_vmedias(handle, org, kubam_ip, oses):
        for os in oses:
            err, msg = UCSCServer.create_virtual_media(handle, org, kubam_ip, os)
            if err != 0:
                return err, msg
        return 0, ""


    @staticmethod
    def list_disks(handle, server):
        """
        Takes in a server object and gets the drives.
        """
        from ucscsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
        from ucscsdk.mometa.compute.ComputeBlade import ComputeBlade
        # Get each controller of the server.
        all_disks = []
        chassis = server["chassis_id"]
        slot = server["slot"]
        domain = server["domain_id"]
        cquery = "(dn, \"compute/sys-{0}/chassis-{1}/blade-{2}/board.*\", type=\"re\")".format(domain, chassis, slot)
        controllers = handle.query_classid("StorageController", cquery)
        # Get the disks of each controller.
        for c in controllers:
            # Get the disks: c.dn: sys/chassis-1/blade-8/board/storage-SAS-1
            dquery = "(dn, \"{0}\", type=\"re\")".format(c.dn)
            disks = handle.query_classid("StorageLocalDisk", dquery)
            for d in disks:
                all_disks.append(d)
        return all_disks

    @staticmethod
    def reset_disks(handle, server):
        from ucscsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk
        
        disks = UCSCServer.list_disks(handle, server)
        for d in disks:
            if d.disk_state == "jbod":
                parent = "/".join(d.dn.split("/")[:-1])
                mo = StorageLocalDisk(
                    parent_mo_or_dn=parent, id=str(d.id),
                    admin_action="unconfigured-good",
                    admin_virtual_drive_id="unspecified",
                    admin_action_trigger="triggered"
                )
                handle.add_mo(mo, True)
                try:
                    handle.commit()
                except UcscException as err:
                    if err.error_code == "103":
                        print "\talready set to unconfigured-good."
                    else:
                        print "error code"
