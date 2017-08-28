import unittest
from iso import IsoMaker

class IsoUnitTests(unittest.TestCase):
    """Tests for `IsoMaker.py`."""
    
    def test_list_isos(self):
        err, isos = IsoMaker.list_isos("/asdf/asd/e/e/efasdf")
        assert(err == 1)
        assert type(isos) is str

if __name__ == '__main__':
    unittest.main()

