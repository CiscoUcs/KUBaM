from imcsdk.imcexception import ImcException
from imc_session import IMCSession
from db import YamlDB
from config import Const
from helper import KubamError


class IMCUtil(object):

    @staticmethod
    def imc_login(server_group):
        """
        login to a IMC and return a login handle
        """
        if not isinstance(server_group, dict):
            raise KubamError("Login format is not correct")
        if "credentials" in server_group:
            credentials = server_group["credentials"]
            if "user" in credentials and "password" in credentials and "ip" in credentials:
                imc_session = IMCSession()
                db = YamlDB()
                err, msg, password = db.decrypt_password(credentials['password'])
                if err == 1:
                    raise KubamError(msg)

                h, msg = imc_session.login(credentials['user'], password, credentials['ip'])
                if msg:
                    raise KubamError(msg)
                if h:
                    return h
                else:
                    raise KubamError("Not logged in into IMC")
            else:
                raise KubamError("The file kubam.yaml does not include the user, password, and IP properties to login.")
        else:
            raise KubamError("IMC Credentials have not been entered.  Please login to IMC to continue.")

    # Logout from the the IMCM
    @staticmethod
    def imc_logout(handle):
        IMCSession.logout(handle)

    # Check if the login was successful
    @staticmethod
    def not_logged_in(msg):
        if msg == "":
            msg = "not logged in to IMC"
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
        imc_session = IMCSession()
        h, err = imc_session.login(user, pw, ip)
        if not h:
            return 1, err
        IMCSession.logout(h)
        return 0, None

    @staticmethod
    def check_imc_login(request):
        if not isinstance(request, dict):
            raise KubamError("improper request sent")
        if 'credentials' not in request:
            raise KubamError ("no credentials found in request")
        for v in ['user', 'password', 'ip']:
            if v not in request['credentials']:
                raise KubamError("credentials should include {0}".format(v))
        user = request['credentials']['user']
        pw = request['credentials']['password']
        ip = request['credentials']['ip']
        if ip == "":
            raise KubamError("Please enter a valid IMCM IP address.")
        imc_session = IMCSession()
        h, err = imc_session.login(user, pw, ip)
        if not h:
            raise KubamError(err)
        IMCSession.logout(h)

    # create org should not have org- prepended to it.
    @staticmethod
    def create_org(handle, org):
        print "Creating Organization: {0}".format(org)
        from imcmsdk.mometa.org.OrgOrg import OrgOrg
        mo = OrgOrg(parent_mo_or_dn="org-root", name=org, descr="KUBAM org")
        handle.add_mo(mo, modify_present=True)
        try:
            handle.commit()
        except ImcException as err:
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

    # Translates the JSON we get from the API to selected servers in the database.
    @staticmethod
    def servers_to_db(imc_servers):
        # Gets a server array list and gets the selected servers and puts them in the database form
        server_pool = dict()
        for s in imc_servers:
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
    def servers_to_api(imc_servers, db_servers):
        for i, real_server in enumerate(imc_servers):
            if real_server['type'] == "blade":
                if "blades" in db_servers:
                    for b in db_servers['blades']:
                        b_parts = b.split("/")
                        if (len(b_parts) == 2 and
                                real_server['chassis_id'] == b_parts[0] and
                                real_server['slot'] == b_parts[1]):
                            real_server['selected'] = True
                            imc_servers[i] = real_server
            elif real_server['type'] == "rack":
                if "rack_servers" in db_servers:
                    for s in db_servers['rack_servers']:
                        if real_server['rack_id'] == s:
                            real_server['selected'] = True
                            imc_servers[i] = real_server
        return imc_servers


    @staticmethod
    def servers_to_objects(objects, servers):
        """
        takes in a bunch of objects: real IMC objects
        and servers: stuff we get from the API like {"blades": [1/1, 2/1], "rack_servers": ["1", "2",...]}
        and filters them
        """
        r_s = [] 
        if "blades" in servers:
            for s in servers["blades"]:
                found = False
                b_parts = s.split("/")
                for real in objects:
                    if not "chassis_id" in real:
                        continue
                    if (real['chassis_id'] ==  b_parts[0] and
                       real['slot'] == b_parts[1] ):
                        found = True
                        r_s.append(real)
                if not found:
                    raise KubamError("server {0} does not exist.".format(s))
        if "rack_servers" in servers:
            for s in servers["rack_servers"]:
                found = False
                for real in objects:
                    if not "rack_id" in real:
                        continue
                    if real['rack_id'] == s:
                        found = True
                        r_s.append(real)
                if not found:
                    raise KubamError("server {0} does not exist.".format(s))
        return r_s

    @staticmethod
    def objects_to_servers(servers, attribs):
        blades = []
        rack_mounts = []
        all_return = {}
        for s in servers:
            parts = [x for x in s["dn"] if x.isdigit()]
            if "chassis" in s["dn"]:
                blades.append("{0}/{1}: {2}".format(parts[0], parts[1], ",".join([ s[p] for p in attribs] )))
            else:
                parts = "".join(parts)
                rack_mounts.append("{0}: {1}".format(parts, ",".join([ s[p] for p in attribs] )))
        if blades:
            all_return["blades"] = blades
        if rack_mounts:
            all_return["rack_servers"] = rack_mounts
        return all_return

    @staticmethod
    def dn_hash_to_out(dn_hash):
        """
        Takes in hash that looks like:
        dn : <properties>
        such as: 
        /sys/chassis-1/blade-1 : { "foo" : "bar", "baz" : "bat" }
        returns the dn in a way the API likes to see it:
        {
           "blades" : 
            [ {"1/1" : {
                "foo" : "bar", 
                "baz" : "bat"
                }
              }
            ],
            "rack_servers":
            [...]
        }
        """
        blades = {}
        rack_mounts = {}
        all_return = {}
        for s in dn_hash.keys():
            parts = [x for x in s if x.isdigit()]
            if "chassis" in s:
                blades["{0}/{1}".format(parts[0], parts[1])] = dn_hash[s]
            else:
                parts = "".join(parts)
                rack_mounts["{0}".format(parts)] = dn_hash[s]
        if blades:
            all_return["blades"] = blades
        if rack_mounts:
            all_return["rack_servers"] = rack_mounts
        return all_return
