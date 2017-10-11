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
    def test_get_network(self):
        err, msg, network = YamlDB.get_network("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_update_network(self):
        err, msg = YamlDB.update_network("/tmp/bfoo.yaml", {"nameserver": "192.168.3.1", "netmask": "255.255.255.0", "gateway": "192.168.1.1"})
        assert(err == 0)
        # make sure that it doesn't let non-valid network configuration through. 
        err, msg = YamlDB.update_network("/tmp/bfoo.yaml", {"netmask": "255.255.255.0", "gateway": "blah"})
        assert(err > 0)
    def test_get_hosts(self):
        err, msg, hosts = YamlDB.get_hosts("/tmp/bfoo.yaml")
        print hosts
        assert(err == 0)
    
    def test_update_hosts(self):
        print self.cfg["hosts"]
        err, msg = YamlDB.update_hosts("/tmp/bfoo.yaml", self.cfg["hosts"])
        assert(err == 0)

    def test_get_public_keys(self):
        err, msg, keys = YamlDB.get_public_keys("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_get_kubam_ip(self):
        err, msg, keys = YamlDB.get_kubam_ip("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_update_kubam_ip(self):
        err, msg = YamlDB.update_kubam_ip("/tmp/bfoo.yaml", "192.168.30.4")
        assert(err == 0)
    
    def test_update_pks(self): 
        err, msg = YamlDB.update_public_keys("/tmp/bfoo.yaml", ["ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDeV4/Sy+B8R21pKzODfGn5W/p9MC9/4ejFUJoI3RlobYOWWxbLmnHYbKmRHn8Jgpmm4xqv61uaFpbAZvxFTyKIqLdcYmxaHem35uzCJbgB8BvT+4aGg1pZREunX6YaE8+s3hFZRu4ti7UHQYWRD1tCizYz78YHL8snp+N3UAPmP9eTTNw62PHAJERi1Hbl6sRfYijqNlluO223Thqbmhtt3S8tnjkRsFnNxsDgxrfbR3GBQ5925hPth3lGejln2P1L9EIQw9NOmtMhF9UpXPWP9r234p3crmBTsw+E6IF0+OsGKOl8Ri4Im7GpnAgbY9I5THEDn142uNOm6vJATZZ3 root@devi-builder"])
        assert(err == 0)
    
    def test_show_config(self):
        err, msg, config = YamlDB.show_config("/tmp/bfoo.yaml")
        #print config
        assert(err == 0)

    def test_get_iso_map(self):
        err, msg, isos = YamlDB.get_iso_map("/tmp/bfoo.yaml")
        assert(err == 0)
    def test_update_iso_map(self):
        err, msg = YamlDB.update_iso_map("/tmp/bfoo.yaml", [{"os" : "centos7.3", "file" : "/Users/vallard/Downloads/kubam/CentOS-7-x86_64-Minimal-1611.iso"}, {"os": "esxi6.0", "file": "/Users/vallard/Downloads/kubam/Vmware-ESXi-6.0.0-5050593-Custom-Cisco-6.0.3.2.iso"}])
        #print msg
        assert(err == 0)
        
        
if __name__ == '__main__':
    unittest.main()

