import unittest
from db import YamlDB

class DBUnitTests(unittest.TestCase):
    """Tests for `Autoinstall.py`."""
    cfg = { "hosts" : [{
            "ip" :  "1.2.3.4" , 
            "name" : "foonode",
            "role" : "k8s master",
            "os" : "esxi6.0" },
            {"ip" :  "1.2.3.5" , 
            "name" : "foonode2",
            "role" : "",
            "os" : "esxi6.0"
            }],
            "network" : {
                "netmask" : "255.255.254.0",
                "gateway" : "192.28.3.4",
                "nameserver" : "172.34.38.1",
                "ntpserver" : "ntp.esl.cisco.com"
            }, 
            "kubam_ip" : "24.2.2.1"
    }
    bad1 = { "foo" : "bar" }
    bad_node = {"name" : "badname", "os" : "bados", "ip": "20" }

    def test_validate_os(self):
        err, msg = YamlDB.validate_os("bad")
        #assert(msg != "")
        #assert(err == 1)
        

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
        err, msg = YamlDB.update_network("/tmp/bfoo.yaml", {"nameserver": "192.168.3.1", "netmask": "255.255.255.0", "gateway": "192.168.1.1", "ntpserver": "ntp.cisco.com"})
        assert(err == 0)
        # make sure that it doesn't let non-valid network configuration through. 
        err, msg = YamlDB.update_network("/tmp/bfoo.yaml", {"netmask": "255.255.255.0", "gateway": "blah"})
        assert(err > 0)
    def test_get_hosts(self):
        err, msg, hosts = YamlDB.get_hosts("/tmp/bfoo.yaml")
        assert(err == 0)
    
    def test_update_hosts(self):
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

    def test_get_proxy(self):
        err, msg, keys = YamlDB.get_proxy("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_update_proxy(self):
        err, msg = YamlDB.update_proxy("/tmp/bfoo.yaml", "https://proxy.esl.cisco.com:80")
        assert(err == 0)
    
    def test_update_pks(self): 
        err, msg = YamlDB.update_public_keys("/tmp/bfoo.yaml", ["ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDeV4/Sy+B8R21pKzODfGn5W/p9MC9/4ejFUJoI3RlobYOWWxbLmnHYbKmRHn8Jgpmm4xqv61uaFpbAZvxFTyKIqLdcYmxaHem35uzCJbgB8BvT+4aGg1pZREunX6YaE8+s3hFZRu4ti7UHQYWRD1tCizYz78YHL8snp+N3UAPmP9eTTNw62PHAJERi1Hbl6sRfYijqNlluO223Thqbmhtt3S8tnjkRsFnNxsDgxrfbR3GBQ5925hPth3lGejln2P1L9EIQw9NOmtMhF9UpXPWP9r234p3crmBTsw+E6IF0+OsGKOl8Ri4Im7GpnAgbY9I5THEDn142uNOm6vJATZZ3 root@devi-builder"])
        assert(err == 0)
    
    def test_show_config(self):
        err, msg, config = YamlDB.show_config("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_get_iso_map(self):
        err, msg, isos = YamlDB.get_iso_map("/tmp/bfoo.yaml")
        assert(err == 0)
    def test_update_iso_map(self):
        err, msg = YamlDB.update_iso_map("/tmp/bfoo.yaml", [{"os" : "centos7.3", "file" : "/Users/vallard/Downloads/kubam/CentOS-7-x86_64-Minimal-1611.iso"}, {"os": "esxi6.0", "file": "/Users/vallard/Downloads/kubam/Vmware-ESXi-6.0.0-5050593-Custom-Cisco-6.0.3.2.iso"}])
        assert(err == 1)
        
    def test_get_org(self):
        err, msg, keys = YamlDB.get_org("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_update_org(self):
        err, msg = YamlDB.update_org("/tmp/bfoo.yaml", "kubam")
        assert(err == 0)

    def test_uuid(self):
        uuid = YamlDB.new_uuid()
        assert(str(uuid))
    def test_server_group(self):
        test_file = "/tmp/k_test"
        if os.path.isfile(test_file):
            os.remove(test_file)
        err, msg = YamlDB.new_server_group("", "")
        assert(err == 1)
        # pass something without a name. 
        err, msg = YamlDB.new_server_group("", {})
        assert(err == 1)
        err, msg = YamlDB.new_server_group("", {'type' : 'beatlejuice'})
        assert(err == 1)
        # no name passed, should generate error
        err, msg = YamlDB.new_server_group("", {'type' : 'imc'})
        assert(err == 1)
        err, msg = YamlDB.new_server_group(test_file, {'type' : 'ucsm', 'name': 'blackbeard'})
        assert(err == 1)
        err, msg = YamlDB.new_server_group(test_file, {'type' : 'ucsm', 'name': 'blackbeard', 'credentials' : 'foo'})
        assert(err == 1)
        err, msg = YamlDB.new_server_group(test_file, {'type' : 'ucsm', 'name': 'blackbeard', 'credentials' : {}})
        assert(err == 1)
        err, msg = YamlDB.new_server_group(test_file, {'type' : 'ucsm', 'name': 'blackbeard', 'credentials' : {'user': 'admin'}})
        assert(err == 1)
        err, msg = YamlDB.new_server_group(test_file, {'type' : 'ucsm', 'name': 'blackbeard', 'credentials' : {'user': 'admin', 'password': 'f00bar'}})
        assert(err == 1)
        # add a new one. This should work as all the credentials are entered in. 
        err, msg = YamlDB.new_server_group(test_file, {'type' : 'ucsm', 'name': 'blackbeard', 'credentials' : {'user': 'admin', 'password': 'f00bar', 'ip': '123.34.23.2'}})
        assert(err == 0)
        # this should fail because it has the same name as the other one.  Names need to be unique
        err, msg = YamlDB.new_server_group(test_file, {'type' : 'ucsm', 'name': 'blackbeard', 'credentials' : {'user': 'admin', 'password': 'f00bar', 'ip': '123.34.23.2'}})
        assert(err == 1)
        # get all the 
        err, msg, sg = YamlDB.list_server_group(test_file)
        assert(err == 0)
        print  sg
        assert(len(sg) == 1)
        # change it
        fg = sg[0]
        # do a copy so we have the object and can manipulate it. 
        bad_group = sg[0].copy()
        bad_group['id'] = "Ilovepeanutbuttersandwiches"
        fg["name"] = "new name"
        # make sure if we try to update something that doesn't exist, it fails. 
        err, msg = YamlDB.update_server_group(test_file, bad_group)
        assert(err == 1)
        err, msg = YamlDB.update_server_group(test_file, fg)
        assert(err == 0)
        err, msg = YamlDB.delete_server_group(test_file, fg["id"])
        assert(err == 0)
    
    def test_decoderkey(self):
        file_name = "/tmp/kubam.yaml"
        err, msg, key = YamlDB.get_decoder_key(file_name)
        assert(err == 0)
    
    def test_aci(self):
        test_file = "/tmp/k_test"
        if os.path.isfile(test_file):
            os.remove(test_file)
        err, msg = YamlDB.new_aci("", "")
        assert(err == 1)
        # pass something without a name. 
        err, msg = YamlDB.new_aci("", {})
        assert(err == 1)
        err, msg = YamlDB.new_aci("", {'name' : 'aci01'})
        assert(err == 1)
        err, msg = YamlDB.new_aci("", {'name' : 'aci01', })
        assert(err == 1)
        err, msg = YamlDB.new_aci(test_file, {'name': 'aci01', 'credentials' : 'foo'})
        assert(err == 1)
        err, msg = YamlDB.new_aci(test_file, {'name': 'aci01', 'credentials' : 'foo'})
        assert(err == 1)
        err, msg = YamlDB.new_aci(test_file, {'name': 'aci01', 'credentials' : {"ip" : "foo"}})
        assert(err == 1)
        err, msg = YamlDB.new_aci(test_file, {'name': 'aci01', 'credentials' : {"ip" : "foo", "user" : "admin"}})
        assert(err == 1)
        err, msg = YamlDB.new_aci(test_file, {'name': 'aci01', 'credentials' : {"ip" : "foo", "user" : "admin", "password" : "password"}})
        assert(err == 1)
        err, msg = YamlDB.new_aci(test_file, {'name': 'aci01', 'credentials' : {"ip" : "foo", "user" : "admin", "password" : "password"}, "tenant_name" : "blue"})
        assert(err == 1)
        err, msg = YamlDB.new_aci(test_file, {'name': 'aci01', 'credentials' : {"ip" : "foo", "user" : "admin", "password" : "password"}, "tenant_name" : "blue", "vrf_name" : "lagoon"})
        assert(err == 1)
        err, msg = YamlDB.new_aci(test_file, {'name': 'aci01', 'credentials' : {"ip" : "foo", "user" : "admin", "password" : "password"}, "tenant_name" : "blue", "vrf_name" : "lagoon", "bridge_domain" : "3"})
        assert(err == 0)
        # get all the 
        err, msg, sg = YamlDB.list_aci(test_file)
        assert(err == 0)
        assert(len(sg) == 1)
        # change it
        fg = sg[0]
        # do a copy so we have the object and can manipulate it. 
        bad_group = sg[0].copy()
        bad_group['id'] = "Ilovepeanutbuttersandwiches"
        fg["name"] = "new name"
        # make sure if we try to update something that doesn't exist, it fails. 
        err, msg = YamlDB.update_aci(test_file, bad_group)
        assert(err == 1)
        err, msg = YamlDB.update_aci(test_file, fg)
        assert(err == 0)
        err, msg = YamlDB.delete_aci(test_file, fg["id"])
        assert(err == 0)
     
    def test_network_group(self):
        test_file = "/tmp/k_test"
        if os.path.isfile(test_file):
            os.remove(test_file)
        err, msg = YamlDB.new_network_group("", "")
        assert(err == 1)
        # pass something without a name. 
        err, msg = YamlDB.new_network_group("", {})
        assert(err == 1)
        err, msg = YamlDB.new_network_group("", {'name' : 'net01'})
        assert(err == 1)
        err, msg = YamlDB.new_network_group("", {'name' : 'net01', })
        assert(err == 1)
        err, msg = YamlDB.new_network_group(test_file, {'name': 'net01', 'netmask' : 'foo'})
        assert(err == 1)
        err, msg = YamlDB.new_network_group(test_file, {'name': 'net01', 'netmask':'255.255.255.0', 'gateway' : '192.168.1.1'})
        assert(err == 1)
        err, msg = YamlDB.new_network_group(test_file, {'name': 'net01', 'netmask':'255.255.255.0', 'gateway' : '192.168.1.1', 'nameserver' : '8.8.8.8'})
        assert(err == 1)
        err, msg = YamlDB.new_network_group(test_file, {'name': 'net01', 'netmask':'255.255.255.0', 'gateway' : '192.168.1.1', 'nameserver' : '8.8.8.8', 'ntpserver' : 'ntp.esl.cisco.com'})
        assert(err == 0)
        # get all the 
        err, msg, sg = YamlDB.list_network_group(test_file)
        assert(err == 0)
        assert(len(sg) == 1)
        # change it
        fg = sg[0]
        # do a copy so we have the object and can manipulate it. 
        bad_group = sg[0].copy()
        bad_group['id'] = "Ilovepeanutbuttersandwiches"
        fg["name"] = "new name"
        # make sure if we try to update something that doesn't exist, it fails. 
        err, msg = YamlDB.update_network_group(test_file, bad_group)
        assert(err == 1)
        err, msg = YamlDB.update_network_group(test_file, fg)
        assert(err == 0)
        err, msg = YamlDB.delete_network_group(test_file, fg["id"])
        assert(err == 0)

    def test_hosts(self):
        test_file = "/tmp/k_test"
        if os.path.isfile(test_file):
            os.remove(test_file)
        err, msg = YamlDB.new_hosts("", "")
        assert(err == 1)
        # pass something without a name. 
        err, msg = YamlDB.new_hosts("", {})
        assert(err == 1)
        err, msg = YamlDB.new_hosts("", [])
        assert(err == 1)
        err, msg = YamlDB.new_hosts(test_file, [{'ip' : '172.20.30.1'}])
        assert(err == 1)
        err, msg = YamlDB.new_hosts(test_file, [{'name': 'kube01', 'ip' : '172.20.30.1'}])
        assert(err == 1)
        err, msg = YamlDB.new_hosts(test_file, [{'name': 'kube01', 'ip' : '172.20.30.1', 'os' : 'centos7.4'}])
        assert(err == 1)
        err, msg = YamlDB.new_hosts(test_file, [{'name': 'kube01', 'ip' : '172.20.30.1', 'os' : 'centos7.4', 'role': 'generic'}])
        assert(err == 0)
        err, msg = YamlDB.new_hosts(test_file, [{'name': 'kube01', 'ip' : '172.20.30.1.1', 'os' : 'centos7.4', 'role': 'generic'}])
        assert(err == 1)
        err, msg = YamlDB.new_hosts(test_file, [{'name': 'kube01 am', 'ip' : '172.20.30.1', 'os' : 'centos7.4', 'role': 'generic'}])
        print ("hostnames should not have spaces in them")
        assert(err == 1)
        err, msg = YamlDB.new_hosts(test_file, [
            {'name': 'kube01', 'ip' : '172.20.30.1', 'os' : 'centos7.4', 'role': 'generic'},
            {'name': 'kube01', 'ip' : '172.20.30.2', 'os' : 'centos7.4', 'role': 'generic'}
            ])
        print ("names should be unique")
        assert(err == 1)
        err, msg = YamlDB.new_hosts(test_file, [
            {'name': 'kube01', 'ip' : '172.20.30.1', 'os' : 'centos7.4', 'role': 'generic'},
            {'name': 'kube02', 'ip' : '172.20.30.1', 'os' : 'centos7.4', 'role': 'generic'}
            ])
        print ("ip addreses should be unique")
        assert(err == 1)

        err, msg = YamlDB.new_hosts(test_file, [
            {'name': 'kube01', 'ip' : '172.20.30.1', 'os' : 'centos7.8', 'role': 'generic'},
            {'name': 'kube02', 'ip' : '172.20.30.2', 'os' : 'centos7.4', 'role': 'generic'}
            ])
        print ("OS should be a supported type")
        assert(err == 1)
        err, msg = YamlDB.new_hosts(test_file, [
            {'name': 'kube01', 'ip': '172.20.30.1', 'os': 'centos7.4', 'role': 'generic'},
            {'name': 'kube02', 'ip': '172.20.30.2', 'os': 'centos7.4', 'role': 'k8s master'}
        ])
        print ("OS should be a supported type")
        assert (err == 0)

if __name__ == '__main__':
    unittest.main()

