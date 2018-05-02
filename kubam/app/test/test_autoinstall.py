import unittest
from autoinstall import Builder


class AutoInstallUnitTests(unittest.TestCase):
    """Tests for autoinstall module."""
    cfg = {
        "hosts": [{
            "ip":  "1.2.3.4",
            "name": "node1",
            # "role" : "k8s master",
            "role": "none",
            "os": "centos7.3"
            }, {
            "ip": "1.2.3.5",
            "name": "node2",
            "role": "k8s node",
            "os": "centos7.3"
            }, {
            "ip": "1.2.3.6",
            "name": "node3",
            "role": "k8s node",
            "os": "centos7.3"
            }
        ],
        "network": {
            "netmask": "255.255.254.0",
            "gateway": "192.28.3.4",
            "nameserver": "172.34.38.1",
            "ntpserver": "1.us.pool.ntp.org"
        },
        "kubam_ip": "24.2.2.1",
        "public_keys": [
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCc/7HrOIZB2wk8FvmZXzLMS1ZJ8TvS9OWBf5xosp59NRvcAb"
            "wbclLRD2f9z5KvOF1n5a4mK03OetymTQQX08rBpZJZ5ZWztdjiFjIce6rm7V87CRjeuwa97XyhacKx98QcijOJW"
            "BbLf1TE/cRd8KVopfG/RPZeMMx1n3J071QRiVhbHEzVw3xuY4KruIb/2kLGHEyYqtx//y8c3k6UaMF180nOIaq6"
            "WBZVHnpYXZZ+EkolpJ+10objpueuWPcJe4OU7AIRP1JGsaDHrmXNoy9ygeWceSqOIqRLOdPneHtC6xU78t3ttpn"
            "RdC9OgtawIVqaq0wpvd7G0sQ7Jv2DO2hZ"
        ]
        
    }
    bad1 = {"foo": "bar"}
    bad_node = {"name": "badname", "os": "bados", "ip": "20"}

    def test_find_template(self):
        node = self.cfg["hosts"][0]
        builder = Builder()
        err, msg, template, template_dir = builder.find_template(node)
    
    # Need to have a template file in ~/kubam/centos7.3.tmpl for this to work.
    def test_build_template(self):
        builder = Builder()
        err, msg, f = builder.build_template(self.cfg["hosts"][0], self.cfg)
        if err != 0:
            print msg
        # print f
        assert(err == 0)


if __name__ == '__main__':
    unittest.main()

