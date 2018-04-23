from app  import app
import unittest
import json

API_ROOT2 = '/api/v2'

class FlaskTestCase(unittest.TestCase):

    def test_api(self):
        tester=app.test_client(self)
        response = tester.get('/', content_type='application/json')
        self.assertEqual(response.status_code,200)


    def test_aci(self):
        tester = app.test_client(self)
 
        response = tester.get(API_ROOT2 + '/aci', content_type='application/json')
        print response.data
        tester.post(API_ROOT2 + '/aci', content_type='application/json')
        print response.data

    def test_host(self):
        tester = app.test_client(self)
        response = tester.get(API_ROOT2 + '/hosts', content_type='application/json')
        print response

    def test_currentsession(self):
        tester = app.test_client(self)
        response = tester.get('/api/v1/session' , content_type='application/json')
        #print response.data
        #self.assertIn(b'REDACTED', response.data)


#    def test_login_correct(self):
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


