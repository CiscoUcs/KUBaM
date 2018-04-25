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

    def test_api(self):
        tester=app.test_client(self)
        response = tester.get('/', content_type='application/json')
        self.assertEqual(response.status_code,200)
    
    def test_server(self):
        tester=app.test_client(self)
        response = tester.post(API_ROOT2 + '/servers', content_type='application/json', data=json.dumps(self.gdata))
        print response.data
        self.assertEqual(response.status_code,201)
        response = tester.get(API_ROOT2 + '/servers', content_type='application/json')
        print response.data
        self.assertEqual(response.status_code,200)
        
    def test_aci(self):
        tester = app.test_client(self)
        response = tester.get(API_ROOT2 + '/aci', content_type='application/json')
        print response.data

#        tester = app.test_client(self)
#        credentials =  { "credentials" : {
#                        "user" : "admin", 
#                         "password" : "nbv12345", 
#                         "server" : "172.28.225.163"
#                        }}
#        response = tester.post(
#                    '/api/v1/session' ,
#                    data = json.dumps(credentials),
#                    content_type='application/json'
#                    )
#        self.assertIn(b'success', response.data)

if __name__ == '__main__':
    unittest.main()


