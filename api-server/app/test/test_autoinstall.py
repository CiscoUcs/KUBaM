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

    def test_find_template(self):
        node = self.cfg["nodes"][0]
        err, msg, template, template_dir = Builder.find_template(node) 

if __name__ == '__main__':
    unittest.main()

