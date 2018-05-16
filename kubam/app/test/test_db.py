import os
import unittest
from db import YamlDB


class DBUnitTests(unittest.TestCase):
    """Tests for `Autoinstall.py`."""
    cfg = {
        "hosts": [{
            "ip":  "1.2.3.4", 
            "name": "foonode",
            "role": "k8s master",
            "os": "esxi6.0"
        }, {
            "ip":  "1.2.3.5",
            "name": "foonode2",
            "roe": "",
            "os": "esxi6.0"
        }],
        "network_groups": [{
            "netmask": "255.255.254.0",
            "gateway": "192.28.3.4",
            "nameserver": "172.34.38.1",
            "ntpserver": "ntp.esl.cisco.com"
        }],
        "kubam_ip": "24.2.2.1"
    }
    bad1 = {"foo": "bar"}
    bad_node = {"name": "badname", "os": "bados", "ip": "20"}

    def __init__(self, *args, **kwargs):
        super(DBUnitTests, self).__init__(*args, **kwargs)
        self.db = YamlDB()

    def test_validate_os(self):
        err, msg = self.db.validate_os("bad")
        # assert(msg != "")
        # assert(err == 1)
        
    def test_validate_ip(self):
        err, msg = self.db.validate_ip("192.168.3.4.5")
        assert(msg != "")
        assert(err == 1)
        err, msg = self.db.validate_ip("192.168.3.4")
        assert(err == 0)

    def test_validate_hosts(self):
        err, msg = self.db.validate_hosts(self.cfg['hosts'])
        assert(err == 0)

    def test_validate_network(self):
        err, msg = self.db.validate_network(self.cfg['network_groups'][0])
        assert(err == 0)

    def test_validate_config(self):
        err, msg, config = self.db.validate_config(self.cfg, True)
        assert(err == 0)
        err, msg, config = self.db.validate_config(self.bad1, True)
        assert(err != 0)

    def test_write_config(self):
        err, msg = self.db.write_config(self.cfg, "/tmp/foo.yaml")
        assert(err == 0)
        err, msg, config = self.db.open_config("/tmp/blah.yaml")
        assert(err == 2)
        err, msg, config = self.db.open_config("/tmp/foo.yaml")
        assert(err == 0)

    def test_get_ucs_vlan(self):
        err, msg, net = self.db.get_ucs_network("/tmp/bfoo.yaml")
        assert(err == 0)
        assert("vlan" in net)


    def test_get_network(self):
        err, msg, network = self.db.get_network("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_update_network(self):
        err, msg = self.db.update_network(
            "/tmp/bfoo.yaml", {
                "nameserver": "192.168.3.1", "netmask": "255.255.255.0", 
                "gateway": "192.168.1.1", "ntpserver": "ntp.cisco.com"
            }
        )
        assert(err == 0)
        # make sure that it doesn"t let non-valid network configuration through. 
        err, msg = self.db.update_network("/tmp/bfoo.yaml", {"netmask": "255.255.255.0", "gateway": "blah"})
        assert(err > 0)

    def test_get_hosts(self):
        err, msg, hosts = self.db.get_hosts("/tmp/bfoo.yaml")
        assert(err == 0)
    
    def test_update_hosts(self):
        err, msg = self.db.update_hosts("/tmp/bfoo.yaml", self.cfg["hosts"])
        assert(err == 0)

    def test_get_public_keys(self):
        err, msg, keys = self.db.get_public_keys("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_get_kubam_ip(self):
        err, msg, keys = self.db.get_kubam_ip("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_update_kubam_ip(self):
        err, msg = self.db.update_kubam_ip("/tmp/bfoo.yaml", "192.168.30.4")
        assert(err == 0)

    def test_get_proxy(self):
        err, msg, keys = self.db.get_proxy("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_update_proxy(self):
        err, msg = self.db.update_proxy("/tmp/bfoo.yaml", "https://proxy.esl.cisco.com:80")
        assert(err == 0)
    
    def test_update_pks(self): 
        err, msg = self.db.update_public_keys(
            "/tmp/bfoo.yaml", [
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDeV4/Sy+B8R21pKzODfGn5W/p9MC9/4ejFUJo"
                "I3RlobYOWWxbLmnHYbKmRHn8Jgpmm4xqv61uaFpbAZvxFTyKIqLdcYmxaHem35uzCJbgB8BvT+4"
                "aGg1pZREunX6YaE8+s3hFZRu4ti7UHQYWRD1tCizYz78YHL8snp+N3UAPmP9eTTNw62PHAJERi1"
                "Hbl6sRfYijqNlluO223Thqbmhtt3S8tnjkRsFnNxsDgxrfbR3GBQ5925hPth3lGejln2P1L9EIQ"
                "w9NOmtMhF9UpXPWP9r234p3crmBTsw+E6IF0+OsGKOl8Ri4Im7GpnAgbY9I5THEDn142uNOm6vJ"
                "ATZZ3 root@devi-builder"
            ]
        )
        assert(err == 0)
    
    def test_show_config(self):
        err, msg, config = self.db.show_config("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_get_iso_map(self):
        err, msg, isos = self.db.get_iso_map("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_update_iso_map(self):
        err, msg = self.db.update_iso_map(
            "/tmp/bfoo.yaml", [
                {
                    "os": "centos7.3",
                    "file": "/Users/vallard/Downloads/kubam/CentOS-7-x86_64-Minimal-1611.iso"
                }, {
                    "os": "esxi6.0",
                    "file": "/Users/vallard/Downloads/kubam/Vmware-ESXi-6.0.0-5050593-Custom-Cisco-6.0.3.2.iso"
                }
            ]
        )
        assert(err == 1)
        
    def test_get_org(self):
        err, msg, keys = self.db.get_org("/tmp/bfoo.yaml")
        assert(err == 0)

    def test_update_org(self):
        err, msg = self.db.update_org("/tmp/bfoo.yaml", "kubam")
        assert(err == 0)

    def test_uuid(self):
        uuid = self.db.new_uuid()
        assert(str(uuid))

    def test_server_group(self):
        test_file = "/tmp/k_test"
        if os.path.isfile(test_file):
            os.remove(test_file)
        err, msg = self.db.new_server_group("", "")
        assert(err == 1)
        # Pass something without a name
        err, msg = self.db.new_server_group("", {})
        assert(err == 1)
        err, msg = self.db.new_server_group("", {"type": "beatlejuice"})
        assert(err == 1)
        # No name passed, should generate error
        err, msg = self.db.new_server_group("", {"type": "imc"})
        assert(err == 1)
        err, msg = self.db.new_server_group(test_file, {"type": "ucsm", "name": "blackbeard"})
        assert(err == 1)
        err, msg = self.db.new_server_group(test_file, {"type": "ucsm", "name": "blackbeard", "credentials": "foo"})
        assert(err == 1)
        err, msg = self.db.new_server_group(test_file, {"type": "ucsm", "name": "blackbeard", "credentials": {}})
        assert(err == 1)
        err, msg = self.db.new_server_group(
            test_file, {"type": "ucsm", "name": "blackbeard", "credentials": {"user": "admin"}}
        )
        assert(err == 1)
        err, msg = self.db.new_server_group(
            test_file, {"type": "ucsm", "name": "blackbeard", "credentials": {"user": "admin", "password": "f00bar"}}
        )
        assert(err == 1)
        # Add a new one, this should work as all the credentials are entered in
        err, msg = self.db.new_server_group(test_file, {
            "type": "ucsm", "name": "blackbeard", "credentials": {
                "user": "admin", "password": "f00bar", "ip": "123.34.23.2"
            }
        })
        assert(err == 0)
        # This should fail because it has the same name as the other one.  Names need to be unique
        err, msg = self.db.new_server_group(test_file, {
            "type": "ucsm", "name": "blackbeard", "credentials": {
                "user": "admin", "password": "f00bar", "ip": "123.34.23.2"
            }
        })
        assert(err == 1)
        err, msg, sg = self.db.list_server_group(test_file)
        assert(err == 0)
        print sg
        assert(len(sg) == 1)
        # Change it
        fg = sg[0]
        # Do a copy so we have the object and can manipulate it
        bad_group = sg[0].copy()
        bad_group['id'] = "Ilovepeanutbuttersandwiches"
        fg['name'] = "new name"
        # Make sure if we try to update something that does not exist, it fails
        err, msg = self.db.update_server_group(test_file, bad_group)
        assert(err == 1)
        err, msg = self.db.update_server_group(test_file, fg)
        assert(err == 0)

        # see that we can get them if there are none. 
        err, msg, servers = self.db.get_ucs_servers(test_file, fg['id'])
        assert(err == 0)
        # see that we can add new blades to the group
        err, msg = self.db.update_ucs_servers(
            test_file, {"blades": ["1/1", "1/2"], "rack_servers": ["7", "8", "9"]}, fg['id']
        )
        assert(err == 0)
        # make sure we actually got new servers
        err, msg, servers = self.db.get_ucs_servers(test_file, fg['id'])
        assert(err == 0)
        assert("blades" in servers)

        err, msg = self.db.delete_server_group(test_file, fg['id'])
        assert(err == 0)
    
    def test_decoderkey(self):
        file_name = "/tmp/kubam.yaml"
        err, msg, key = self.db.get_decoder_key(file_name)
        assert(err == 0)
    
    def test_aci(self):
        test_file = "/tmp/k_test"
        if os.path.isfile(test_file):
            os.remove(test_file)
        err, msg = self.db.new_aci("", "")
        assert(err == 1)
        # Pass something without a name
        err, msg = self.db.new_aci("", {})
        assert(err == 1)
        err, msg = self.db.new_aci("", {"name": "aci01"})
        assert(err == 1)
        err, msg = self.db.new_aci("", {"name": "aci01", })
        assert(err == 1)
        err, msg = self.db.new_aci(test_file, {"name": "aci01", "credentials": "foo"})
        assert(err == 1)
        err, msg = self.db.new_aci(test_file, {"name": "aci01", "credentials": "foo"})
        assert(err == 1)
        err, msg = self.db.new_aci(test_file, {"name": "aci01", "credentials": {"ip": "foo"}})
        assert(err == 1)
        err, msg = self.db.new_aci(test_file, {"name": "aci01", "credentials": {"ip": "foo", "user": "admin"}})
        assert(err == 1)
        err, msg = self.db.new_aci(
            test_file, {"name": "aci01", "credentials": {"ip": "foo", "user": "admin", "password": "password"}}
        )
        assert(err == 1)
        err, msg = self.db.new_aci(test_file, {
            "name": "aci01", 
            "credentials": {
                "ip": "foo", "user": "admin", "password": "password"
            }, 
            "tenant_name": "blue"
        })
        assert(err == 1)
        err, msg = self.db.new_aci(test_file, {
            "name": "aci01",
            "credentials": {
                "ip": "foo", "user": "admin", "password": "password"
            }, 
            "tenant_name": "blue",
            "vrf_name": "lagoon"
        })
        assert(err == 1)
        err, msg = self.db.new_aci(test_file, {
            "name": "aci01",
            "credentials": {
                "ip": "foo", "user": "admin", "password": "password"
            }, 
            "tenant_name": "blue", 
            "vrf_name": "lagoon", 
            "bridge_domain": "3"})
        assert(err == 0)
        err, msg, sg = self.db.list_aci(test_file)
        assert(err == 0)
        assert(len(sg) == 1)
        # Change it
        fg = sg[0]
        # Do a copy so we have the object and can manipulate it
        bad_group = sg[0].copy()
        bad_group['id'] = "Ilovepeanutbuttersandwiches"
        fg['name'] = "new name"
        # Make sure if we try to update something that does not exist, it fails
        err, msg = self.db.update_aci(test_file, bad_group)
        assert(err == 1)
        err, msg = self.db.update_aci(test_file, fg)
        assert(err == 0)
        err, msg = self.db.delete_aci(test_file, fg['id'])
        assert(err == 0)
     
    def test_network_group(self):
        test_file = "/tmp/k_test"
        if os.path.isfile(test_file):
            os.remove(test_file)
        err, msg = self.db.new_network_group("", "")
        assert(err == 1)
        # Pass something without a name
        err, msg = self.db.new_network_group("", {})
        assert(err == 1)
        err, msg = self.db.new_network_group("", {"name": "net01"})
        assert(err == 1)
        err, msg = self.db.new_network_group("", {"name": "net01", })
        assert(err == 1)
        err, msg = self.db.new_network_group(test_file, {"name": "net01", "netmask": "foo"})
        assert(err == 1)
        err, msg = self.db.new_network_group(
            test_file, {"name": "net01", "netmask": "255.255.255.0", "gateway": "192.168.1.1"}
        )
        assert(err == 1)
        err, msg = self.db.new_network_group(test_file, {
            "name": "net01", "netmask": "255.255.255.0", "gateway": "192.168.1.1", "nameserver": "8.8.8.8"
        })
        assert(err == 1)
        err, msg = self.db.new_network_group(test_file, {
            "name": "net01", "netmask": "255.255.255.0", "gateway": "192.168.1.1",
            "nameserver": "8.8.8.8", "ntpserver": "ntp.esl.cisco.com"
        })
        assert(err == 0)
        err, msg, sg = self.db.list_network_group(test_file)
        assert(err == 0)
        assert(len(sg) == 1)
        # Change it
        fg = sg[0]
        # Do a copy so we have the object and can manipulate it.
        bad_group = sg[0].copy()
        bad_group['id'] = "Ilovepeanutbuttersandwiches"
        fg['name'] = "new name"
        # Make sure if we try to update something that does not exist, it fails
        err, msg = self.db.update_network_group(test_file, bad_group)
        assert(err == 1)
        err, msg = self.db.update_network_group(test_file, fg)
        assert(err == 0)
        err, msg = self.db.delete_network_group(test_file, fg['id'])
        assert(err == 0)

    def test_hosts(self):
        test_file = "/tmp/k_test"
        if os.path.isfile(test_file):
            os.remove(test_file)
        # First create a network to test with.
        err, msg = self.db.new_network_group(test_file, {
            "name": "net01", "netmask": "255.255.255.0", "gateway": "192.168.1.1",
            "nameserver": "8.8.8.8", "ntpserver": "ntp.esl.cisco.com"
        })
        assert(err == 0)
        err, msg, nets = self.db.list_network_group(test_file)
        assert(err == 0)
        assert(len(nets) == 1)
        net = nets[0]
        net_id = net['id']
        err, msg = self.db.new_hosts("", "")
        assert(err == 1)
        # Pass something without a name
        err, msg = self.db.new_hosts("", {})
        assert(err == 1)
        err, msg = self.db.new_hosts("", [])
        assert(err == 1)
        err, msg = self.db.new_hosts(test_file, [{"ip": "172.20.30.1"}])
        assert(err == 1)
        err, msg = self.db.new_hosts(test_file, [{"name": "kube01", "ip": "172.20.30.1"}])
        assert(err == 1)
        err, msg = self.db.new_hosts(test_file, [{"name": "kube01", "ip": "172.20.30.1", "os": "centos7.4"}])
        assert(err == 1)
        err, msg = self.db.new_hosts(
            test_file, [{"name": "kube01", "ip": "172.20.30.1", "os": "centos7.4", "role": "generic"}]
        )
        assert(err == 1)
        err, msg = self.db.new_hosts(
            test_file, [{"name": "kube01", "ip": "172.20.30.1.1", "os": "centos7.4", "role": "generic"}]
        )
        assert(err == 1)
        err, msg = self.db.new_hosts(
            test_file, [{"name": "kube01 am", "ip": "172.20.30.1", "os": "centos7.4", "role": "generic"}]
        )
        print ("hostnames should not have spaces in them")
        assert(err == 1)
        err, msg = self.db.new_hosts(test_file, [
            {"name": "kube01", "ip": "172.20.30.1", "os": "centos7.4", "role": "generic"},
            {"name": "kube01", "ip": "172.20.30.2", "os": "centos7.4", "role": "generic"}
        ])
        print ("names should be unique")
        assert(err == 1)
        err, msg = self.db.new_hosts(test_file, [
            {"name": "kube01", "ip": "172.20.30.1", "os": "centos7.4", "role": "generic"},
            {"name": "kube02", "ip": "172.20.30.1", "os": "centos7.4", "role": "generic"}
        ])
        print ("ip addreses should be unique")
        assert(err == 1)

        err, msg = self.db.new_hosts(test_file, [
            {"name": "kube01", "ip": "172.20.30.1", "os": "centos7.8", "role": "generic"},
            {"name": "kube02", "ip": "172.20.30.2", "os": "centos7.4", "role": "generic"}
        ])
        print ("OS should be a supported type")
        assert(err == 1)
        good_array = [
            {"name": "kube01", "ip": "172.20.30.1", "os": "centos7.4", "role": "generic", "network_group": net_id},
            {"name": "kube02", "ip": "172.20.30.2", "os": "centos7.4", "role": "k8s master", "network_group": net_id}
        ]
        err, msg = self.db.new_hosts(test_file, good_array)
        print ("network should always have a network_group associated")
        assert (err == 0)
        err, msg = self.db.delete_network_group(test_file, net_id)
        assert(err == 0)


if __name__ == "__main__":
    unittest.main()
