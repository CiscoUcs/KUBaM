from ucsc_session import UCSCSession
from db import YamlDB
from helper import KubamError


class UCSCUtil(object):

    @staticmethod
    def ucsc_login(server_group):
        """
        login to a UCS and return a login handle
        """
        if not isinstance(server_group, dict):
            raise KubamError("Login format is not correct")
        if "credentials" in server_group:
            credentials = server_group["credentials"]
            if "user" in credentials and "password" in credentials and "ip" in credentials:
                ucs_session = UCSCSession()
                db = YamlDB()
                err, msg, password = db.decrypt_password(credentials['password'])
                if err == 1:
                    raise KubamError(msg)

                h, msg = ucs_session.login(credentials['user'], password, credentials['ip'])
                if msg:
                    raise KubamError(msg)
                if h:
                    return h
                else:
                    raise KubamError("Not logged in into UCS")
            else:
                raise KubamError("The file kubam.yaml does not include the user, password, and IP properties to login.")
        else:
            raise KubamError("UCS Credentials have not been entered.  Please login to UCS to continue.")

    # Logout from the the UCSM
    @staticmethod
    def ucsc_logout(handle):
        UCSCSession.logout(handle)

    # Check if the login was successful
    @staticmethod
    def not_logged_in(msg):
        if msg == "":
            msg = "not logged in to UCS"
        return msg

    @staticmethod
    def check_ucsc_login(request):
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
            raise KubamError("Please enter a valid UCSM IP address.")
        ucsc_session = UCSCSession()
        h, err = ucsc_session.login(user, pw, ip)
        if not h:
            raise KubamError(err)
        UCSCSession.logout(h)

    @staticmethod
    def objects_to_servers(servers, attribs):
        blades = []
        rack_mounts = []
        all_return = {}
        for s in servers:
            parts = [x for x in s["dn"] if x.isdigit()]
            if "chassis" in s["dn"]:
                b = parts[-1]
                c = parts[-2]
                d = "".join(parts[:-2])
                blades.append("{0}/{1}/{2}: {3}".format(d, c, b, ",".join([ s[p] for p in attribs] )))
            else:
                d = "".join(parts[0:4])
                r = "".join(parts[4:])
                rack_mounts.append("{0}/{1}: {2}".format(d, r, ",".join([ s[p] for p in attribs] )))
        if blades:
            all_return["blades"] = blades
        if rack_mounts:
            all_return["rack_servers"] = rack_mounts
        return all_return

    @staticmethod
    def servers_to_objects(objects, servers):
        """
        take in all of the UCS objects and filter out the ones the API 
        passed into us and return a list with just the servers we wanted. 
        """
        r_s = []
        if "blades" in servers:
            for s in servers["blades"]:
                found = False
                b_parts = s.split("/")
                for real in objects:
                    if not "chassis_id" in real:
                        continue
                    if (real['domain_id'] == b_parts[0] and
                        real['chassis_id'] ==  b_parts[1] and
                       real['slot'] == b_parts[2] ):
                        found = True
                        r_s.append(real)
                if not found:
                    raise KubamError("server {0} does not exist: {1}".format(s, b_parts))
        if "rack_servers" in servers:
            for s in servers["rack_servers"]:
                found = False
                r_parts = s.split("/")
                for real in objects:
                    if not "rack_id" in real:
                        continue
                    if (real['domain_id'] == r_parts[0] and 
                        real['rack_id'] == r_parts[1]):
                        found = True
                        r_s.append(real)
                if not found:
                    raise KubamError("server {0} does not exist!".format(s))
        return r_s
