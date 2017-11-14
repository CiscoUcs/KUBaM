import unittest
from session import UCSSession

class SessionUnitTests(unittest.TestCase):
    """Tests for `UCSServer.py`."""
    handle, err = UCSSession.login("admin",
                                   "nbv12345",
                                   "172.28.225.163")

    def test_serverlist(self):
        msg = UCSSession.ensure_version(self.handle)
        assert(msg == "")
        version = UCSSession.get_version(self.handle)
        assert(version.startswith('3'))
