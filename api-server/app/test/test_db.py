import unittest
from db import YamlDB

class DBUnitTests(unittest.TestCase):
    """Tests for `Autoinstall.py`."""
    cfg = { "hosts" : [{
            "ip" :  "1.2.3.4" , 
            "name" : "foonode",
            "os" : "esxi6.0" },
            {"ip" :  "1.2.3.5" , 
            "name" : "foonode2",
            "os" : "esxi6.0"
            }],
            "network" : {
                "netmask" : "255.255.254.0",
                "gateway" : "192.28.3.4",
                "nameserver" : "172.34.38.1"
            }, 
            "kubam_ip" : "24.2.2.1"
    }
    bad1 = { "foo" : "bar" }
    bad_node = {"name" : "badname", "os" : "bados", "ip": "20" }

    def test_validate_os(self):
        err, msg = YamlDB.validate_os("bad")
        assert(msg != "")
        assert(err == 1)
        

    def test_validate_ip(self):
        err, msg = YamlDB.validate_ip("192.168.3.4.5")
        assert(msg != "")
        assert(err == 1)
        err, msg = YamlDB.validate_ip("192.168.3.4")
        assert(err == 0)

    def test_validate_hosts(self):
        err, msg = YamlDB.validate_hosts(self.cfg["hosts"])
        assert(err == 0)

    def test_validate_network(self):
        err, msg = YamlDB.validate_network(self.cfg["network"])
        assert(err == 0)

    def test_validate_config(self):
        err, msg, config = YamlDB.validate_config(self.cfg, True)
        assert(err == 0)
        err, msg, config = YamlDB.validate_config(self.bad1, True)
        assert(err != 0)
    def test_write_config(self):
        err, msg = YamlDB.write_config(self.cfg, "/tmp/foo.yaml")
        assert(err == 0)
    def test_open_config(self):
        err, msg, config = YamlDB.open_config("/tmp/blah.yaml")
        assert(err == 2)
        err, msg, config = YamlDB.open_config("/tmp/foo.yaml")
        assert(err == 0)
    def test_add_credentials(self):
        err, msg = YamlDB.update_ucs_creds("/tmp/bfoo.yaml", {"ip": "172.28.225.163", "user": "admin", "password": "nbv12345"})
        assert(err == 0)
        err, msg = YamlDB.update_ucs_creds("/tmp/bfoo.yaml", {"ip": "172.28.225.164", "user": "admin", "password": "nbv12345"})
        
    def test_add_ucs_vlan(self):
        err, msg = YamlDB.update_ucs_network("/tmp/bfoo.yaml", {"vlan": "default"})
        assert(err == 0)
    def test_add_ucs_servers(self):
        err, msg = YamlDB.update_ucs_servers("/tmp/bfoo.yaml", {"blades": ["1/1", "1/2"], "rack_servers": ["7", "8", "9"]})
        assert(err == 0)
    def test_get_ucs_vlan(self):
        err, msg, net = YamlDB.get_ucs_network("/tmp/bfoo.yaml")
        assert(err == 0)
        assert("vlan" in net)

    def test_get_ucs_servers(self):
        err, msg, servers = YamlDB.get_ucs_servers("/tmp/bfoo.yaml")
        assert(err == 0)
        assert("blades" in servers)
    
        
        
if __name__ == '__main__':
    unittest.main()

