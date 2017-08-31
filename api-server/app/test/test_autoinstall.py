import unittest
from autoinstall import Builder

class AutoInstallUnitTests(unittest.TestCase):
    """Tests for `Autoinstall.py`."""
    cfg = { "nodes" : [{
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
            "masterIP" : "24.2.2.1"
    }
    bad1 = { "foo" : "bar" }
    bad_node = {"name" : "badname", "os" : "bados", "ip": "20" }

    def test_validate_os(self):
        err, msg = Builder.validate_os("bad")
        assert(msg != "")
        assert(err == 1)
        

    def test_validate_ip(self):
        err, msg = Builder.validate_ip("192.168.3.4.5")
        assert(msg != "")
        assert(err == 1)
        err, msg = Builder.validate_ip("192.168.3.4")
        assert(err == 0)

    def test_validate_nodes(self):
        err, msg = Builder.validate_nodes(self.cfg["nodes"])
        assert(err == 0)

    def test_validate_network(self):
        err, msg = Builder.validate_network(self.cfg["network"])
        assert(err == 0)

    def test_validate_config(self):
        err, msg, config = Builder.validate_config(self.cfg)
        assert(err == 0)
        err, msg, config = Builder.validate_config(self.bad1)
        print msg
        assert(err != 0)

    def test_find_template(self):
        node = self.cfg["nodes"][0]
        err, msg, template, template_dir = Builder.find_template(node) 

if __name__ == '__main__':
    unittest.main()

