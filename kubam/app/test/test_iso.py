import unittest
from autoinstall import IsoMaker


class IsoUnitTests(unittest.TestCase):
    """Tests for `iso_maker.py`."""

    def test_list_isos(self):
        err, isos = IsoMaker.list_isos("/asdf/asd/e/e/efasdf")
        assert(err == 1)
        assert type(isos) is str


if __name__ == '__main__':
    unittest.main()

