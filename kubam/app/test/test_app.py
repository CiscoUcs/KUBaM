from app import app
import unittest
import json

API_ROOT2 = '/api/v2'

class FlaskTestCase(unittest.TestCase):
    gdata = {
        "credentials" : { 
            "ip": "10.93.234.238", "password": "oicu812!", "user": "admin"
        },
       "type": "ucsm", 
       "name": "werners machine"
    }

    newnet = {
        "router" : "192.168.1.1",
        "netmask" : "255.255.255.0",
        "dnsserver": "8.8.8.8",
        "ntpserver" : "ntp.cisco.com",
        "vlan" : "5"
    }
    newaci = {
        "name" : "acitest", 
        "credentials" : { 
            "ip" : "foo", "user" : "admin", "password" : "password"
        }, 
        "tenant_name" : "blue", 
        "vrf_name" : "lagoon", 
        "bridge_domain" : "3"
    }

    def test_api(self):
        tester=app.test_client(self)
        response = tester.get('/', content_type='application/json')
        self.assertEqual(response.status_code,200)
    
    def test_server(self):
        tester=app.test_client(self)
        response = tester.post(API_ROOT2 + '/servers', content_type='application/json', data=json.dumps(self.gdata))
        print response.data
        #self.assertEqual(response.status_code,201)
        response = tester.get(API_ROOT2 + '/servers', content_type='application/json')
        print response.data
        self.assertEqual(response.status_code,200)
        d = json.loads(response.get_data(as_text=True))
        delete_me = ""
        for a in  d['servers']:
            if a['name'] == self.gdata['name']:
                delete_me = a
        if not delete_me == "":
            tester.delete(API_ROOT2 + '/servers', content_type='application/json', data=json.dumps({"id" : delete_me['id']}))

    def test_network(self):
        tester=app.test_client(self)
        response = tester.post(API_ROOT2+'/networks', content_type='application/json', data=json.dumps(self.newnet))
        self.assertEqual(response.status_code,400)
        response = tester.get(API_ROOT2+'/networks', content_type='capplication/json')
        print response
        
    def test_aci(self):
        tester = app.test_client(self)
        response = tester.post(API_ROOT2+'/aci', content_type='application/json', data=json.dumps(self.newaci))
        print response.data
        response = tester.get(API_ROOT2 + '/aci', content_type='application/json')
        d = json.loads(response.get_data(as_text=True))
        dAci = ""
        for a in  d['aci']:
            if a['name'] == self.newaci['name']:
                dAci = a
        if not dAci == "":
            tester.delete(API_ROOT2 + '/aci', content_type='application/json', data=json.dumps({"id" : dAci['id']}))
            

                
        
#        self.assertIn(b'success', response.data)

if __name__ == '__main__':
    unittest.main()


