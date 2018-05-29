from helper import KubamError
from ucscsdk.ucscexception import UcscException


class UCSCServer(object):
    
    @staticmethod
    def list_templates(handle):

        filter_str = "(type, 'initial-template', type='eq') or (type, 'updating-template', type='eq')"
        try:
            query = handle.query_classid("lsServer", filter_str=filter_str)
            templates = list()

            for q in query:
                templates.append({"name": q.name})
            return templates

        except UcsException as e:
            raise KubamError(e)


    @staticmethod
    def create_server(handle, template, name, org):
        """
        Create a new service profile from a template that already exist.
        Must use the dn for the template: org-root/ls-TestTemplate
        """
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
            #if err.error_code == "105":
            #    print "\t" + sp_name + " already exists."
            #else:
            #    return 1, err.error_descr
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
        except UcsException as err:
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
        except UcsException as err:
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
