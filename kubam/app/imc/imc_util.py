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
