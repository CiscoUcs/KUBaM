from imcsdk.imchandle import ImcHandle, ImcException
from imcsdk.imcexception import ImcOperationError
from helper import KubamError
import socket
from urllib2 import HTTPError


class IMCSession(object):
    # Get the current firmware version.  Returns something like: 3.1(2b)
    def login(self, username, password, server):
        # Test if the server reachable
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(20)
        try:
            result = s.connect_ex((server, 443))
            if result != 0:
                return None, "{0} on port 443 is not reachable".format(server)
            s.close()
        except socket.error as err:
            return None, "IMC Login Error: {0} {1}".format(server, err.strerror)

        handle = ImcHandle(server, username, password, auto_refresh=True, force=True)
        try:
            handle.login()
        except ImcException as err:
            print "Login Error: " + err.error_descr
            return None, err.error_descr
        except HTTPError as err:
            print "Connection Error: Bad IMCM? " + err.reason
            return None, err.reason
        except Exception as e:
            print "Issue logging in. Please check that all parameters are correct"
            print e
            return None, "Issue logging in. Please check that all parameters are correct."

        msg = self.ensure_version(handle)
        return handle, msg

    @staticmethod
    def logout(handle):
        try:
            handle.logout()
        except ImcException as e:
            raise KubamError(str(e))
