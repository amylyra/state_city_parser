import re
import sys
import csv
import os

city_zip_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    "../../../staging/zipcode-city.csv")
state_name_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    "../../../staging/state_names.tsv")


class InvalidAddressException(Exception):
    pass


class ParseAddress(object):
    def __init__(self, cities=None, states=None, zips=None):
        self.city_zip_map, self.state_zip_map = self.load_city_state_zip_map(city_zip_file)
        self.state_names = self.load_state_name_map(state_name_file)
        self.inv_state_names = {v_i: k for k, v in self.state_names.iteritems() for v_i in v}
        self.city_state_map = self.load_city_state_map(city_zip_file)
        if cities:
            for c in self.city_zip_map:
                    if c not in cities:
                        self._delete_key(self.city_zip_map, self.city_zip_map[c])

        if states:
            for s in self.state_zip_map:
                if s not in states:
                    self._delete_key(self.state_zip_map, self.state_zip_map[s])

        if zips:
            for z in self.city_zip_map:
                if z not in zips:
                    self._delete_key(self.city_zip_map, z)
            for z in self.state_zip_map:
                if z not in zips:
                    self._delete_key(self.state_zip_map, z)

    def parse_address(self, address):
        return Address(address, self)

    def load_city_state_zip_map(self, filename):
        city_zip_map = {}
        state_zip_map = {}
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",", quoting=csv.QUOTE_NONE)
            for row in reader:
                if row['LocationType'] == "NOT ACCEPTABLE":
                    continue
                try:
                    city_zip_map[row['Zipcode']]
                except KeyError:
                    city_zip_map[row['Zipcode']] = []
                    state_zip_map[row['Zipcode']] = []
                city_zip_map[row['Zipcode']].append(row['City'])
                state_zip_map[row['Zipcode']].append(row['State'])
        return city_zip_map, state_zip_map

    def load_city_state_map(self, filename):
        city_state_map = {}
        with open(filename) as f:
            reader = csv.DictReader(f, delimiter=',', quoting=csv.QUOTE_NONE)
            for row in reader:
                if row['LocationType'] == "NOT ACCEPTABLE":
                    continue
                city_state_map[row['City']] = row['State']
        return city_state_map

    def load_state_name_map(self, filename):
        state_name_map = {}
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t", quoting=csv.QUOTE_NONE)
            for row in reader:
                name = row["Name"].strip().upper().replace(".", "")
                aliases = filter(None, row["Aliases"].strip().upper().replace('.', '').split(','))
                postal_code = row["Postal Code"].strip().upper().replace('.', '')
                state_name_map[postal_code] = aliases + [name] + [postal_code]
        return state_name_map

    def _delete_key(self, dicti, key):
        del dicti[key]


class Address(object):
    def __init__(self, addr, parser):
        self.zip = None
        self.state = None
        self.city = None
        self.parser = parser
        self.comma_seperated_address = None
        self.buffer = None

        address = self.preprocess_address(addr)

        self.parse_address(address)

        error_string = ''
        if not self.zip:
            error_string = "Address %s missing zipcode."
        if not self.state:
            error_string = "Address %s missing state."
        if not self.city:
            error_string = "Address %s missing city."

    def preprocess_address(self, address, cities=None, zips=None, states=None):
        address = address.replace("# ", "#")
        address = address.replace(" &", "&")
        address = address.replace("-", " ")
        address = re.sub(r"\,\s*\,", ",", address)
        address = address.strip().replace(".", "")
        self.comma_seperated_address = address.split(",")
        address = address.replace(",", " ")
        address = address.replace(";", " ")
        return address

    def parse_address(self, addr):
        address = reversed(addr.split())
        unmatched = []

        for token in address:
            token = token.strip().upper()
            if self.find_zip(token):
                continue
            if self.find_state(token):
                continue
            if self.find_city(token):
                continue
            if self.guess_unmatched(token):
                continue
            self.buffer = token
            unmatched.append(token)
        return unmatched

    def find_zip(self, token):
        if not self.zip:
            guess = re.search(r"\d{5}", token)
            if guess:
                guess = guess.group(0)
            try:
                a = self.parser.city_zip_map[guess]
                self.zip = guess
                return True
            except KeyError:
                pass
        return False

    def find_state(self, token):
        if not self.zip:
            return False
        guess_list = list(set(self.parser.state_zip_map[self.zip]))
        token_alternative = self._alternative_name(token)
        for g in guess_list:
            for s in self.parser.state_names[g]:
                if token == s or token_alternative == s:
                    self.state = g
                    return True
        return False

    def find_city(self, token):
        if not self.zip:
            return False
        guess_list = self.parser.city_zip_map[self.zip]
        for g in guess_list:
            if token == g or self._alternative_name(token) == g:
                self.city = g
                return True
        return False

    def guess_unmatched(self, token):
        """NO Zip found or Zip does not match with city or state
           Bruteforce search City and State, issue Warning
           First search longer string
        """
        if self.zip and self.state and self.city:
            return True

        token_alternative = self._alternative_name(token)

        _state = self.find_state_by_name(token)
        _state_alternative = self.find_state_by_name(token_alternative)
        _state_bycity = self.find_state_by_city()

        if token != token_alternative:
            if _state_alternative:
                self.state = _state_alternative
            elif _state_bycity:
                self.state = _state_bycity
            else:
                pass

            for c in list(self.parser.city_state_map.keys()):
                if c == token_alternative:
                    self.city = c
                    break

        if not self.city:
            for c in list(self.parser.city_state_map.keys()):
                if c == token:
                    self.city = c

        _state_bycity = self.find_state_by_city()

        if not self.state:
            if _state:
                self.state = _state
            elif _state_bycity:
                self.state = _state_bycity
            else:
                pass

        pass

    def find_state_by_name(self, token):
        try:
            return self.parser.inv_state_names[token]
        except KeyError:
            pass
        return None

    def _alternative_name(self, token):
        if self.buffer:
            return ("%s %s" % (token, self.buffer)).upper()
        return token

    def find_state_by_city(self):
        if not self.city:
            return None
        try:
            return self.parser.city_state_map[self.city]
        except KeyError:
            return None

        return None
