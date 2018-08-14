from app import app
import unittest
import json
from config import Const


class FlaskTestCase(unittest.TestCase):
    gdata = {
        "credentials": {
            "ip": "10.93.130.108", "password": "admin", "user": "admin"
        },
        "type": "ucsm",
        "name": "LL1-UCS-3-FI-VIP"
    }

    newnet = {
        "name": "newnet",
        "gateway": "192.168.1.1",
        "netmask": "255.255.255.0",
        "nameserver": "8.8.8.8",
        "ntpserver": "ntp.cisco.com",
        "vlan": "5"
    }

    newaci = {
        "name": "acitest",
        "credentials": {
            "ip": "foo", "user": "admin", "password": "password"
        }, 
        "tenant_name": "blue",
        "vrf_name": "lagoon",
        "bridge_domain": "3"
    }

    newhosts = [
        {'name': 'kube01', 'ip': '172.20.30.1', 'os': 'centos7.4', 'role': 'generic', 'network_group': 'HOLD'},
        {'name': 'kube02', 'ip': '172.20.30.2', 'os': 'centos7.4', 'role': 'k8s master', 'network_group': 'HOLD'}
    ]

    def test_api(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_server(self):
        tester = app.test_client(self)
        response = tester.post(
            Const.API_ROOT2 + '/servers', content_type='application/json',
            data=json.dumps(self.gdata)
        )
        print response.data
        self.assertEqual(response.status_code, 201)
        response = tester.get(Const.API_ROOT2 + '/servers', content_type='application/json')
        # print response.data
        self.assertEqual(response.status_code, 200)
        d = json.loads(response.get_data(as_text=True))
        delete_me = None
        for a in d['servers']:
            if a['name'] == self.gdata['name']:
                delete_me = a
        if delete_me:
            response = tester.delete(
                Const.API_ROOT2 + '/servers', content_type='application/json', data=json.dumps({"name": delete_me['name']})
            )
            self.assertEqual(response.status_code, 204)
        else: 
            print "test server group not found.  Should have been found and deleted."

    def test_network(self):
        tester = app.test_client(self)
        response = tester.post(
            Const.API_ROOT2+'/networks', content_type='application/json', data=json.dumps(self.newnet)
        )
        self.assertEqual(response.status_code, 201)
        response = tester.get(Const.API_ROOT2+'/networks', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        d = json.loads(response.get_data(as_text=True))
        delete_me = None
        for a in d['networks']:
            if a['name'] == self.newnet['name']:
                delete_me = a
        if delete_me:
            response = tester.delete(
                Const.API_ROOT2 + '/networks', content_type='application/json',
                data=json.dumps({"name": delete_me['name']})
            )
            self.assertEqual(response.status_code, 201)
        else:
            print "test network name not found. SHould have been found and deleted."

    def test_aci(self):
        tester = app.test_client(self)
        response = tester.post(Const.API_ROOT2+'/aci', content_type='application/json', data=json.dumps(self.newaci))
        # Make sure it was able to create it
        self.assertEqual(response.status_code, 201)
        # print response.data
        response = tester.get(Const.API_ROOT2 + '/aci', content_type='application/json')
        d = json.loads(response.get_data(as_text=True))
        d_aci = None
        for a in d['aci']:
            if a['name'] == self.newaci['name']:
                d_aci = a
        if d_aci:
            response = tester.delete(
                Const.API_ROOT2 + '/aci', content_type='application/json', data=json.dumps({"name": d_aci['name']})
            )
            self.assertEqual(response.status_code, 201)
        else: 
            print "aci name not found and not deleted.  Shoudl have been"

    def test_hosts(self):
        tester = app.test_client(self)
        # First get a network
        response = tester.delete(
            Const.API_ROOT2 + '/networks', content_type='application/json', data=json.dumps({"name": self.newnet['name']})
        )
        response = tester.post(
            Const.API_ROOT2+'/networks', content_type='application/json', data=json.dumps(self.newnet)
        )
        self.assertEqual(response.status_code, 201)
        response = tester.get(Const.API_ROOT2+'/networks', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        d = json.loads(response.get_data(as_text=True))
        first_net = d['networks'][0]
        # Add the id into the hosts
        for h in self.newhosts:
            h["network_group"] = first_net['name']
        response = tester.post(
            Const.API_ROOT2+'/hosts', content_type='application/json', data=json.dumps(self.newhosts)
        )
        self.assertEqual(response.status_code, 201)
        
        # shouldn't be able to delete this network
        response = tester.delete(
            Const.API_ROOT2 + '/networks', content_type='application/json', data=json.dumps({"name": first_net['name']})
        )
        # should be 400 because the 2 hosts are using this network. 
        self.assertEqual(response.status_code, 400)

        response = tester.delete(
            Const.API_ROOT2+'/hosts', content_type='application/json', data=json.dumps({"name": self.newhosts[0]['name']})
        )
        self.assertEqual(response.status_code, 201)

        response = tester.delete(
            Const.API_ROOT2+'/hosts', content_type='application/json', data=json.dumps({"name": self.newhosts[1]['name']})
        )
        self.assertEqual(response.status_code, 201)

        # hosts are gone, should delete network
        response = tester.delete(
            Const.API_ROOT2 + '/networks', content_type='application/json', data=json.dumps({"name": first_net['name']})
        )
        self.assertEqual(response.status_code, 201)



if __name__ == '__main__':
    unittest.main()
