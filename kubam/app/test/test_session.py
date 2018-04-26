import unittest
from ucs import UCSSession


class SessionUnitTests(unittest.TestCase):
    """Tests for `ucs_server.py`."""
    ucs_session = UCSSession()
    handle, err = ucs_session.login("admin",
                                   "nbv12345",
                                   "172.28.225.163")

    def test_serverlist(self):
        session = UCSSession()
        msg = session.ensure_version(self.handle)
        assert(msg == "")
        version = session.get_version(self.handle)
        assert(version.startswith('3'))
