import unittest
from address_parser import ParseAddress

testStates = {
    "888 N Kingston St. APT 1, San Mateo, CA, 94401": "CA",
    "123123 a;lsdfj as;dlkf, San Francisco, CA, 94103": "CA",
    "12312 sdfasdoiuwer, Burlingame, CA, 94010": "CA",
    "12312 sdfasdoiuwer, Burlingame, CA, 99999": "CA",
    "12312 sdfasdoiuwer, Green Bay": "WI",
    "Visalia": "CA",
    "West Virginia": "WV"
}

testCity = {
    "999 N Kingston St. , San Mateo, CA, 94401": "San Mateo",
    "123123 a;lsdfj as;dlkf, San Francisco, CA, 94103": "San Francisco"
}

testZip = {
    "244 N spante St. APT 1, San Mateo, CA, 94401": "94401",
    "123123 a;lsdfj as;dlkf, San Francisco, CA, 94103": "94103"
}


class TestAddressParser(unittest.TestCase):

    def test_parser_state(self):
        for addr, case in testStates.iteritems():
            pa = ParseAddress().parse_address(addr)
            self.assertEqual(pa.state, case.upper())

    def test_parser_city(self):
        for addr, case in testCity.iteritems():
            pa = ParseAddress().parse_address(addr)
            self.assertEqual(pa.city, case.upper())

    def test_parser_zip(self):
        for addr, case in testZip.iteritems():
            pa = ParseAddress().parse_address(addr)
            self.assertEqual(pa.zip, case)


if __name__ == '__main__':
    unittest.main()
