from unittest import mock
from application.routes import app
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
    "parameters": {
        "search_type": "bankruptcy",
        "counties": ["ALL"],
        "search_items": [{
            "name": "Bob Howard"
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
    "parameters": {
        "search_type": "full",
        "counties": ["ALL"],
        "search_items": [{
            "name": "Jasper Beer",
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
    "parameters": {
        "search_type": "bankruptcy",
        "counties": ["ALL"],
        "search_items": [{"name": "King Stark of the North",
                          "complex_no": "1000167"}]
    }
})

complex_name_search_data_full_all = json.dumps({
    "customer": {
        "key_number": "1234567",
        "name": "Dave The Customer",
        "address": "Lurking",
        "reference": "someRef"
    },
    "document_id": 17,
    "parameters": {
        "search_type": "full",
        "counties": ["ALL"],
        "search_items": [{"name": "Jasper Beer",
                          "year_from": 1925,
                          "year_to": 2015
                          },
                         {"name": "King Stark of the North",
                          "complex_no": "1000167",
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
    "parameters": {
        "search_type": "full",
        "counties": ["Devon"],
        "search_items": [{
            "name": "Jasper Beer",
            "year_from": 1925,
            "year_to": 2015
        }]
    }
})

search_data = [{"id": 76, "registration_date": datetime.date(2005, 12, 2), "application_type": "PAB",
                "registration_no": "50135"}]
all_queries_data = [{
    "registration_no": "50000", "registration_date": "2012-08-09",
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
    "amends": None,
    "key_number": "1234567",
    "county": "Devon",
    "document_ref": 22,
    "postcode": "PL1 1AA",
    "cancelled_by": None,
    "original_regn_no": "7",
    "extra_data": {}
}]

all_queries_complex_data = [{
    "registration_no": "50027", "registration_date": "2012-08-09",
    "application_type": "PAB", "id": "56", "debtor_reg_name_id": "12",
    "forename": "", "register_id": "2",
    "middle_names": "",
    "surname": "",
    "complex_number": 1234567,
    "complex_name": "King Stark",
    "occupation": "",
    "trading_name": "",
    "application_reference": "123456789",
    "legal_body": "LB", "legal_body_ref": "Moo",
    "line_1": "123 The Street",
    "line_2": "Somewhere",
    "line_3": "",
    "line_4": "",
    "line_5": "",
    "line_6": "",
    "amends": None,
    "key_number": "1234567",
    "county": "Devon",
    "document_ref": 22,
    "postcode": "PL1 1AA",
    "cancelled_by": None,
    "original_regn_no": "7",
    "extra_data": {}
}]

mock_search = fetchboth_mock([1], search_data)
mock_search_not_found = fetchboth_mock([1], [])
mock_migration = fetchboth_mock(["50001"], ["50001"])
mock_retrieve = fetchboth_mock(all_queries_data, all_queries_data)
mock_retrieve_complex = fetchboth_mock(all_queries_complex_data, all_queries_complex_data)
mock_cancellation = fetchboth_mock(['50001'], [['50001']])
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
    def test_item_found(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_search_data, headers=headers)
        data = json.loads(response.data.decode('utf-8'))
        assert response.status_code == 200
        assert 76 in data[0]['Bob Howard']

    @mock.patch('psycopg2.connect', **mock_search)
    def test_full_search_all_counties(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_search_data_full_all, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **mock_search)
    def test_complex_name_simple_search(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=complex_name_search_data, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **mock_search)
    def test_complex_name_full_search_all_counties(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=complex_name_search_data_full_all, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **mock_search)
    def test_full_search_some_counties(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_search_data_full_counties, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **mock_search_not_found)
    def test_item_not_found(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_search_data, headers=headers)
        data = json.loads(response.data.decode('utf-8'))
        assert response.status_code == 200
        assert len(data[0]['Bob Howard']) == 0

    @mock.patch('psycopg2.connect', **mock_search_not_found)
    def test_search_bad_data(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data='{"foo": "bar"}', headers=headers)
        assert response.status_code == 400

    @mock.patch('psycopg2.connect')
    def test_search_not_json(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.post('/search', data=name_search_data, headers=headers)
        assert response.status_code == 415

    @mock.patch('psycopg2.connect')
    def test_not_json(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.post('/registration', data=valid_data, headers=headers)
        assert response.status_code == 415

    @mock.patch('psycopg2.connect')
    @mock.patch('kombu.Producer.publish')
    def test_new_registration(self, mock_connect, mock_publish):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/registration', data=valid_data, headers=headers)
        assert response.status_code == 200
        assert mock_publish.called

    @mock.patch('psycopg2.connect')
    @mock.patch('kombu.Producer.publish')
    def test_new_registration_complex_name(self, mock_connect, mock_publish):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/registration', data=valid_data_complex, headers=headers)
        assert response.status_code == 200
        assert mock_publish.called

    @mock.patch('psycopg2.connect', **mock_migration)
    def test_migration_success(self, mc):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/migrated_record', data=migration_data, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect')
    def test_migration_invalid(self, mc):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/migrated_record', data='{"cheese": "brie"}', headers=headers)
        assert response.status_code == 400

    @mock.patch('psycopg2.connect', **mock_cancellation)
    def test_cancellation(self, mc):
        response = self.app.delete('/registration/50001', data='{}', headers={'Content-Type': 'application/json'})
        data = json.loads(response.data.decode('utf-8'))
        assert data['cancelled'][0] == '50001'

    @mock.patch('psycopg2.connect', **mock_cancellation)
    @mock.patch('kombu.Producer.publish')
    def test_amendment(self, mc, kombu):
        response = self.app.put('/registration/50001', data=valid_data,
                                headers={'Content-Type': 'application/json'})
        data = json.loads(response.data.decode('utf-8'))
        amendment_call = mock_cancellation['return_value'].mock_calls[-4].call_list()

        # Because the DB is mocked, we can't check to ensure the indicator's gone on
        # But we can check that the correct SQL call has been issued...
        sql_call = str(amendment_call[0])
        assert "UPDATE register_details SET cancelled_by" in sql_call  # Ensure we're looking at the right call
        assert "'canc': '50001'" in sql_call  # mock_cancellation returns 50001 for all the queries
        assert "'id': '50001'" in sql_call
        assert data['new_registrations'][0] == 50002
        assert data['amended_registrations'][0] == '50001'

    @mock.patch('psycopg2.connect', **mock_search_not_found)
    def test_amendment_not_found(self, mc):
        response = self.app.put('/registration/50001/amend', data=valid_data,
                                headers={'Content-Type': 'application/json'})
        assert (response.status_code == 404)

    @mock.patch('psycopg2.connect', **mock_retrieve)
    def test_get_registration(self, mc):
        response = self.app.get("/registration/50000")
        data = json.loads(response.data.decode('utf-8'))
        assert data['debtor_name']['surname'] == 'Howard'
        assert "document_id" in data

    @mock.patch('psycopg2.connect', **mock_retrieve_complex)
    def test_get_registration_complex_name(self, mc):
        response = self.app.get("/registration/50027")
        data = json.loads(response.data.decode('utf-8'))
        assert data['complex']['name'] == 'King Stark'
        assert "document_id" in data

    @mock.patch('psycopg2.connect', **mock_retrieve)
    def test_get_migrated_registration(self, mc):
        response = self.app.get("/migrated_registration/500")
        data = json.loads(response.data.decode('utf-8'))
        assert data[0]['debtor_name']['surname'] == 'Howard'

    @mock.patch('psycopg2.connect', **mock_counties)
    def test_get_counties(self, mc):
        response = self.app.get("/counties")
        data = json.loads(response.data.decode('utf-8'))
        assert len(data) == 3
        assert data[1] == 'COUNTY2'
