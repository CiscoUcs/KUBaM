import unittest
from monitor import ucsc_fsm
from ucs import UCSServer, UCSSession
from ucsc import UCSCServer, UCSCSession, UCSCMonitor

class MonitorUnitTests(unittest.TestCase):
    """Tests for `ucs_server.py`."""

    def test_ucsc_fsm(self):
        session = UCSCSession()
        handle, err = session.login("admin", "Cisco.123", "10.93.140.102")
        assert(err == None)
        out = handle.rawXML('''
<configRemoteResolveChildren
    cookie="{3}"
    inDn="sys/chassis-{1}/blade-{2}/fsm"
    inDomainId="{0}"
    inHierarchical="true">
        <inFilter>
        </inFilter>
</configRemoteResolveChildren>'''.format("1009", "1", "3", handle.cookie))
        UCSCSession.logout(handle)
    
if __name__ == '__main__':
    unittest.main()
