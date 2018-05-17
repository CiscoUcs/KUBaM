from ucscsdk.ucschandle import UcscHandle
from ucscsdk.ucscexception import UcscException
from helper import KubamError
import socket
from urllib2 import HTTPError


class UCSCSession(object):
    # Get the current firmware version.  Returns something like: 3.1(2b)

    # Returns handle or error message
    def login(self, username, password, server):
        handle = UcscHandle(server, username, password)
        try:
            handle.login()
        except UcscException as err:
            print "Login Error: " + err.error_descr
            return None, err.error_descr
        except HTTPError as err:
            print "Connection Error: Bad UCSC? " + err.reason
            return None, err.reason
        except Exception as e:
            print "Issue logging in. Please check that all parameters are correct"
            print e
            return None, "Issue logging in. Please check that all parameters are correct."

        return handle, None

    @staticmethod
    def logout(handle):
        try:
            handle.logout()
        except UcscException as e:
            raise KubamError(str(e))
