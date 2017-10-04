import unittest
from server import UCSServer
from session import UCSSession

class ServerUnitTests(unittest.TestCase):
    """Tests for `UCSServer.py`."""
    handle, err = UCSSession.login("admin",
                                   "nbv12345",
                                   "172.28.225.163")

    def test_serverlist(self):
        servers = UCSServer.list_servers(self.handle)
        for s in servers:
            print s
        assert(servers != "")
