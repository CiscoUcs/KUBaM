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
    def ucs_logout(handle):
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

