import unittest
from ucs import UCSServer, UCSSession


class ServerUnitTests(unittest.TestCase):
    """Tests for `ucs_server.py`."""
    ucs_session = UCSSession()
    handle, err = ucs_session.login("admin",
                                   "nbv12345",
                                   "172.28.225.163")

    def test_serverlist(self):
        servers = UCSServer.list_servers(self.handle)
        #print servers
        assert(servers != "")

    def test_list_blade(self):
        s = "1/1"
        blade = UCSServer.list_blade(self.handle, s)
        #print blade
        #print blade.oper_state
        disks = UCSServer.list_disks(self.handle, blade)
        #print disks
#    def test_delete_servers(self):
#        err, msg = UCSServer.deleteKubeServers(self.handle, "org-root/org-kubam", [{"name" : "kubamTest01"}])
#        print msg
#        assert(err == 0)
    def test_create_service_profile_template(self):
        UCSServer.create_service_profile_template(this.handle, "org-root")

