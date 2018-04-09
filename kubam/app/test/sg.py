import unittest
from servergroup import sg

class SGUnitTests(unittest.TestCase):
    """Tests for Server Group Tests."""
    # {"name", "ucs01", "type" : "ucsm", "credentials" : {"user": "admin", "password" : "secret-password", "ip" : "172.28.225.163" }}
    newsg = { 
            "name" : "sjc",
            "type" : "ucsm",
            "credentials" : {
                "user" : "admin",
                "password" : "nbv12345",
                "ip": "172.28.225.163"
            } 
    }
    
    def test_newsg(self):
        err, msg = sg.create(self.newsg)
        assert(msg != "")
        assert(err != 1)

if __name__ == '__main__':
    unittest.main()

