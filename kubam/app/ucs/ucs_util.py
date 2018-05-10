from ucsmsdk.ucsexception import UcsException
from ucs_session import UCSSession
from db import YamlDB
from config import Const


class UCSUtil(object):
    # Login to the UCSM
    @staticmethod
    def ucs_login():
        db = YamlDB()
        err, msg, config = db.open_config(Const.KUBAM_CFG)
        if err == 0:
            if "ucsm" in config and "credentials" in config['ucsm']:
                credentials = config['ucsm']['credentials']
                if "user" in credentials and "password" in credentials and "ip" in credentials:
                    ucs_session = UCSSession()
                    h, msg = ucs_session.login(credentials['user'], credentials['password'], credentials['ip'])
                    if msg:
                        return 1, msg, None
                    if h:
                        return 0, msg, h
                    return 1, msg, None
                else:
                    msg = "kubam.yaml file does not include the user, password, and ip properties to login."
                    err = 1
            else:
                msg = "UCS Credentials have not been entered.  Please login to UCS to continue."
                err = 1
        return err, msg, None

    # Logout from the the UCSM
    @staticmethod
    def ucs_logout(handle):
        UCSSession.logout(handle)

    # Check if the login was successful
    @staticmethod
    def not_logged_in(msg):
        if msg == "":
            msg = "not logged in to UCS"
        return msg

    @staticmethod
    def check_aci_login(request):
        if 'credentials' not in request:
            return 1, "no credentials found in request"
        for v in ['user', 'password', 'ip']:
            if v not in request['credentials']:
                return 1, "credentials should include {0}".format(v)
        user = request['credentials']['user']
        pw = request['credentials']['password']
        ip = request['credentials']['ip']
        if ip == "":
            return 1, "Please enter a valid ACI IP address."

        # TODO: implement ACI APIs to log in and configure
        ucs_session = UCSSession()
        h, err = ucs_session.login(user, pw, ip)
        if not h:
            return 1, err
        UCSSession.logout(h)
        return 0, None

    @staticmethod
    def check_ucs_login(request):
        if not isinstance(request, dict):
            return 1, "improper request sent"
        if 'credentials' not in request:
            return 1, "no credentials found in request"
        for v in ['user', 'password', 'ip']:
            if v not in request['credentials']:
                return 1, "credentials should include {0}".format(v)
        user = request['credentials']['user']
        pw = request['credentials']['password']
        ip = request['credentials']['ip']
        if ip == "":
            return 1, "Please enter a valid UCSM IP address."
        ucs_session = UCSSession()
        h, err = ucs_session.login(user, pw, ip)
        if not h:
            return 1, err
        UCSSession.logout(h)
        return 0, None

    # create org should not have org- prepended to it.
    @staticmethod
    def create_org(handle, org):
        print "Creating Organization: {0}".format(org)
        from ucsmsdk.mometa.org.OrgOrg import OrgOrg
        mo = OrgOrg(parent_mo_or_dn="org-root", name=org, descr="KUBAM org")
        handle.add_mo(mo, modify_present=True)
        try:
            handle.commit()
        except UcsException as err:
            if err.error_code == "103":
                print "\tOrganization already exists."
            else:
                return 1, err.error_descr
        return 0, ""

    # org should not have org-<name> prepended."
    @staticmethod
    def query_org(handle, org):
        print "Checking if org {0} exists".format(org)
        obj = handle.query_dn("org-root/org-" + org)
        if not obj:
            print "Org {0} does not exist".format(org)
            return False
        else:
            print "Org {0} exists.".format(org)
            return True

    # org should be passed with the org-<name> prepended to it.
    @staticmethod
    def delete_org(handle, org):
        print "Deleting Org {0}".format(org)
        mo = handle.query_dn(org)
        try:
            handle.remove_mo(mo)
            handle.commit()
        except AttributeError:
            print "\talready deleted"

    def get_full_org(self, handle):
        db = YamlDB()
        err, msg, org = db.get_org(Const.KUBAM_CFG)
        if err != 0:
            return err, msg, org
        if org == "":
            org = "kubam"

        if org == "root":
            full_org = "org-root"
        else:
            full_org = "org-root/org-" + org

        if org != "root":
            err, msg = self.create_org(handle, org)
        return err, msg, full_org

    # Translates the JSON we get from the web interface to what we expect to put in the database
    @staticmethod
    def servers_to_db(ucs_servers):
        # Gets a server array list and gets the selected servers and puts them in the database form
        server_pool = dict()
        for s in ucs_servers:
            if "selected" in s and s['selected']:
                if s['type'] == "blade":
                    if "blades" not in server_pool:
                        server_pool['blades'] = []
                    b = "{0}/{1}".format(s['chassis_id'], s['slot'])
                    server_pool["blades"].append(b)
                elif s['type'] == "rack":
                    if "rack_servers" not in server_pool:
                        server_pool['rack_servers'] = []
                    server_pool['rack_servers'].append(s['rack_id'])
        return server_pool

    # See if there are any selected servers in the database
    @staticmethod
    def servers_to_api(ucs_servers, db_servers):
        for i, real_server in enumerate(ucs_servers):
            if real_server['type'] == "blade":
                if "blades" in db_servers:
                    for b in db_servers['blades']:
                        b_parts = b.split("/")
                        if (len(b_parts) == 2 and
                                real_server['chassis_id'] == b_parts[0] and
                                real_server['slot'] == b_parts[1]):
                            real_server['selected'] = True
                            ucs_servers[i] = real_server
            elif real_server['type'] == "rack":
                if "rack_servers" in db_servers:
                    for s in db_servers['rack_servers']:
                        if real_server['rack_id'] == s:
                            real_server['selected'] = True
                            ucs_servers[i] = real_server
        return ucs_servers
