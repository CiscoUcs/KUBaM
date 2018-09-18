import unittest
from disks import Disks
from ucs import UCSServer, UCSSession
from ucsc import UCSCServer, UCSCSession


class DiskUnitTests(unittest.TestCase):
    """Tests for `ucs_server.py`."""
    
    def est_list_disks(self):
        ucs_session = UCSSession()
        handle, err = ucs_session.login("admin", "admin", "10.93.130.107")
        s = {"blades" : ["1/1"]} 
        d, rc = Disks.list_ucsm(handle, s)
        assert(rc == 200)
        ucs_session.logout(handle)
    
    def est_reset_disks(self):
        ucs_session = UCSSession()
        handle, err = ucs_session.login("admin", "admin", "10.93.130.107")
        s = {"blades" : ["1/1"]} 
        d, rc = Disks.delete_ucsm(handle, s)
        ucs_session.logout(handle)

    def test_list_disks_ucsc(self):
        session = UCSCSession()
        handle, err = session.login("admin", "Cisco.123", "10.93.140.102")
        s = {"blades" : ["1009/1/3"]} 
        d, rc = Disks.list_ucsc(handle, s)
        print d
        assert(rc == 200)
        session.logout(handle)
        

if __name__ == '__main__':
    unittest.main()
