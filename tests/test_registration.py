from unittest import mock
from application.routes import app
from application.data_diff import get_rectification_type, is_name_change_type3
import os
import json
import datetime
import psycopg2


def fetchall_mock(data):
    return {
        'return_value': mock.Mock(**{
            'cursor.return_value': mock.Mock(**{'fetchall.return_value': data})
        })
    }


def fetchone_mock(data):
    return {
        'return_value': mock.Mock(**{
            'cursor.return_value': mock.Mock(**{'fetchone.return_value': data})
        })
    }


def fetchboth_mock(data_one, data_all):
    return {
        'return_value': mock.Mock(**{
            'cursor.return_value': mock.Mock(**{
                'fetchone.return_value': data_one,
                'fetchall.return_value': data_all
            })
        })
    }


directory = os.path.dirname(__file__)
valid_data = open(os.path.join(directory, 'data/valid_data.json'), 'r').read()
valid_data_complex = open(os.path.join(directory, 'data/valid_data_complex.json'), 'r').read()
migration_data = open(os.path.join(directory, 'data/migrator.json'), 'r').read()
name_data = '{"forenames": "Bob Oscar Francis", "surname": "Howard", "full_name": "Bob Oscar Francis Howard", ' \
            '"search_type": "banks"}'
name_search_data = json.dumps({
    "customer": {
        "key_number": "1234567",
        "name": "Dave The Customer",
        "address": "Lurking",
        "reference": "someRef"
    },
    "document_id": 17,
    "expiry_date": "2013-01-01",
    "search_date": "2012-01-01",
    "parameters": {
        "search_type": "banks",
        "counties": ["ALL"],
        "search_items": [{
            "name_type": "Private Individual",
            "name": {
                "forenames": "Casper",
                "surname": "Beers"
            },
        }]
    }
})

name_search_data_full_all = json.dumps({
    "customer": {
        "key_number": "1234567",
        "name": "Dave The Customer",
        "address": "Lurking",
        "reference": "someRef"
    },
    "document_id": 17,
    "expiry_date": "2013-01-01",
    "search_date": "2012-01-01",
    "parameters": {
        "search_type": "full",
        "counties": ["ALL"],
        "search_items": [{
            "name_type": "Private Individual",
            "name": {
                "forenames": "Jasper",
                "surname": "Beers"
            },
            "year_from": 1925,
            "year_to": 2015
        }]
    }
})

complex_name_search_data = json.dumps({
    "customer": {
        "key_number": "1234567",
        "name": "Dave The Customer",
        "address": "Lurking",
        "reference": "someRef"
    },
    "document_id": 17,
    "expiry_date": "2013-01-01",
    "search_date": "2012-01-01",
    "parameters": {
        "search_type": "banks",
        "counties": ["ALL"],
        "search_items": [{"complex_name": "King Stark of the North",
                          "complex_number": "1000167",
                          "name_type": "Complex Name",}]
    }
})

complex_name_search_data_full_all = json.dumps({
    "customer": {
        "key_number": "1234567",
        "name": "Dave The Customer",
        "address": "Lurking",
        "reference": "someRef"
    },
    "expiry_date": "2013-01-01",
    "search_date": "2012-01-01",
    "document_id": 17,
    "parameters": {
        "search_type": "full",
        "counties": ["ALL"],
        "search_items": [{"name": {"forenames": "Bob", "surname": "Beer"},
                          "name_type": "Private Individual",
                          "year_from": 1925,
                          "year_to": 2015
                          },
                         {"complex_name": "King Stark of the North",
                          "complex_number": "1000167",
                          "name_type": "Complex Name",
                          "year_from": 1925,
                          "year_to": 2015}]
    }
})

name_search_data_full_counties = json.dumps({
    "customer": {
        "key_number": "1234567",
        "name": "Dave The Customer",
        "address": "Lurking",
        "reference": "someRef"
    },
    "document_id": 17,
    "expiry_date": "2013-01-01",
    "search_date": "2012-01-01",
    "parameters": {
        "search_type": "full",
        "counties": ["Devon"],
        "search_items": [{
            "name_type": "Private Individual",
            "name": {"forenames": "Jasper", "surname": "Beer"},
            "year_from": 1925,
            "year_to": 2015
        }]
    }
})

search_data = [{"id": 76, "registration_date": datetime.date(2005, 12, 2), "application_type": "PAB",
                "registration_no": "50135"}]

all_queries_data = [{
    "registration_no": "50000",
    "registration_date": datetime.datetime(2012, 8, 9),
    "reg": 50001,
    "date": datetime.datetime(2013, 8, 9),
    "class_of_charge": "PAB",
    "application_type": "PAB", "id": "56", "debtor_reg_name_id": "12",
    "forename": "Bob", "register_id": "2",
    "middle_names": "Oscar Francis",
    "surname": "Howard",
    "complex_number": None,
    "complex_name": "",
    "occupation": "Civil Servant",
    "trading_name": "Bob",
    "application_reference": "123456789",
    "legal_body": "LB", "legal_body_ref": "Moo",
    "line_1": "123 The Street",
    "line_2": "Somewhere",
    "line_3": "",
    "line_4": "",
    "line_5": "",
    "line_6": "",
    "reveal": True,
    "amendment_type": "",
    "address_type": "Debtor Residence", "address_string": "",
    "amends": None,
    "key_number": "1234567",
    "county": "Devon",
    "customer_name": "Bob", "customer_address": "Place",
    "name": "Devon",
    "party_type": "Estate Owner",
    "name_type_ind": "Private Individual",
    "county_id": 22,
    "document_ref": 22,
    "postcode": "PL1 1AA",
    "cancelled_by": None,
    "additional_info": "", "district": "", "short_description": "",
    "original_regn_no": "7",
    "extra_data": {},
    "details_id": 528
}]

all_queries_complex_data = [{
    "registration_no": "50027",
    "registration_date": datetime.datetime(2012, 8, 9),
    "date": datetime.datetime(2013, 8, 9),
    "class_of_charge": "PAB",
    "application_type": "PAB", "id": "56", "debtor_reg_name_id": "12",
    "forename": "", "register_id": "2",
    "middle_names": "",
    "surname": "",
    "complex_number": 1234567,
    "complex_name": "King Stark",
    "customer_name": "Bob", "customer_address": "Place",
    "occupation": "",
    "name": "Devon",
    "trading_name": "",
    "application_reference": "123456789",
    "legal_body": "LB", "legal_body_ref": "Moo",
    "line_1": "123 The Street",
    "line_2": "Somewhere",
    "line_3": "",
    "line_4": "",
    "line_5": "",
    "reveal": True,
    "amendment_type": "",
    "party_type": "Estate Owner",
    "line_6": "",
    "name_type_ind": "Complex Name",
    "address_type": "Debtor Residence", "address_string": "",
    "amends": None,
    "key_number": "1234567",
    "county": "Devon",
    "document_ref": 22,
    "county_id": 22,
    "postcode": "PL1 1AA",
    "cancelled_by": None,
    "original_regn_no": "7",
    "additional_info": "", "district": "", "short_description": "",
    "extra_data": {}
}]

mock_search = fetchboth_mock([1], search_data)
mock_search_not_found = fetchboth_mock([1], [])
mock_migration = fetchboth_mock(["50001"], ["50001"])
mock_retrieve = fetchboth_mock(all_queries_data, all_queries_data)
mock_retrieve_complex = fetchboth_mock(all_queries_complex_data, all_queries_complex_data)
#mock_cancellation = fetchboth_mock(['50001'], [['50001']])
mock_counties = fetchall_mock([
    {'name': 'COUNTY1'},
    {'name': 'COUNTY2'},
    {'name': 'COUNTY3'},
])


class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **mock_search)
    def test_full_search_all_counties(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/searches', data=name_search_data_full_all, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **mock_search)
    def test_full_search_some_counties(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/searches', data=name_search_data_full_counties, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **mock_search_not_found)
    def test_search_bad_data(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/searches', data='{"foo": "bar"}', headers=headers)
        assert response.status_code == 400

    @mock.patch('psycopg2.connect')
    def test_search_not_json(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.post('/searches', data=name_search_data, headers=headers)
        assert response.status_code == 415

    @mock.patch('psycopg2.connect')
    def test_not_json(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.post('/registrations', data=valid_data, headers=headers)
        assert response.status_code == 415

    @mock.patch('psycopg2.connect', **mock_retrieve)
    def test_get_registration(self, mc):
        response = self.app.get("/registrations/2015-01-01/50000")
        data = json.loads(response.data.decode('utf-8'))
        assert data['parties'][0]['names'][0]['private']['surname'] == 'Howard'

    @mock.patch('psycopg2.connect', **mock_search_not_found)
    def test_get_registration_404(self, mc):
        response = self.app.get("/registrations/2015-01-01/50000")
        assert response.status_code == 404

    @mock.patch('psycopg2.connect', **mock_retrieve_complex)
    def test_get_registration_complex_name(self, mc):
        response = self.app.get("/registrations/2015-01-01/50027")
        print(response.data)
        data = json.loads(response.data.decode('utf-8'))
        assert data['parties'][0]['names'][0]['complex']['name'] == 'King Stark'

    def test_name_type_identification(self):
        assert is_name_change_type3({"forenames": ["John", "David"], "surname": "Smyth"},
                                    {"forenames": ["John", "David"], "surname": "Smith"}) == False

        assert is_name_change_type3({"forenames": ["J"], "surname": "Smith"},
                                    {"forenames": ["John", "David"], "surname": "Smith"}) == False

        assert is_name_change_type3({"forenames": ["John", "D"], "surname": "Smith"},
                                    {"forenames": ["John", "David"], "surname": "Smith"}) == False

        assert is_name_change_type3({"forenames": ["John"], "surname": "Smith"},
                                    {"forenames": ["John", "David"], "surname": "Smith"}) == False

        assert is_name_change_type3({"forenames": ["J", "D"], "surname": "Smith"},
                                    {"forenames": ["John", "David"], "surname": "Smith"}) == True

        assert is_name_change_type3({"forenames": [], "surname": "Smith"},
                                    {"forenames": ["John", "David"], "surname": "Smith"}) == True

    def test_rectification_type(self):
        assert get_rectification_type({'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["John", "David"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Devon']}, 'class_of_charge': 'C1'},
                                      {'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["John", "David"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Devon']}, 'class_of_charge': 'C1'}) == 1

        assert get_rectification_type({'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["Sam", "John"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Devon']}, 'class_of_charge': 'C1'},
                                      {'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["John", "David"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Devon']}, 'class_of_charge': 'C1'}) == 2

        assert get_rectification_type({'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["John", "David"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Devon']}, 'class_of_charge': 'C1'},
                                      {'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["John", "David"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Devon', 'Dorset']}, 'class_of_charge': 'C1'}) == 2

        assert get_rectification_type({'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["John", "David"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Devon']}, 'class_of_charge': 'C1'},
                                      {'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["John", "David"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Dorset']}, 'class_of_charge': 'C1'}) == 3

        assert get_rectification_type({'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["John", "David"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Devon']}, 'class_of_charge': 'C1'},
                                      {'parties': [{'names': [{'type': 'Private Individual', "private": {"forenames": ["John", "David"], "surname": "Smith"}}]}],
                                       'particulars': {'counties': ['Devon']}, 'class_of_charge': 'C4'}) == 3


