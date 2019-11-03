from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.ucsexception import UcsException
from helper import KubamError
import socket
from urllib2 import HTTPError


class UCSSession(object):
    # Get the current firmware version.  Returns something like: 3.1(2b)
    @staticmethod
    def get_version(handle):
        dn = "sys/mgmt/fw-system"
        firmware = handle.query_dn(dn)
        return firmware.version

    def ensure_version(self, handle):
        version = self.get_version(handle)
        if version.startswith('3') or version.startswith('4'):
            return None
        return "Unsupported UCS firmware version: {0}. Please update to at least 3.0".format(version)

    # Returns handle or error message
    def login(self, username, password, server):
        # Test if the server reachable
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        try:
            result = s.connect_ex((server, 80))
            if result != 0:
                return None, "{0} is not reachable".format(server)
            s.close()
        except socket.error as err:
            return None, "UCS Login Error: {0} {1}".format(server, err.strerror)

        handle = UcsHandle(server, username, password)
        try:
            handle.login()
        except UcsException as err:
            print "Login Error: " + err.error_descr
            return None, err.error_descr
        except HTTPError as err:
            print "Connection Error: Bad UCSM? " + err.reason
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
        except UcsException as e:
            raise KubamError(str(e))
