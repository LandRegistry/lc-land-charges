from unittest import mock
from application.routes import app
import os
import json
import datetime


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
migration_data = open(os.path.join(directory, 'data/migrator.json'), 'r').read()
name_data = '{"forenames": "Bob Oscar Francis", "surname": "Howard"}'


search_data = [{"id": 1, "registration_date": datetime.date(2005, 12, 2), "application_type": "PAB",
                "registration_no": "50135"}]
all_queries_data = [{
    "registration_no": "50000", "registration_date": "2012-08-09",
    "application_type": "PAB", "id": "56", "debtor_reg_name_id": "12",
    "forename": "Bob", "register_id": "2",
    "middle_names": "Oscar Francis",
    "surname": "Howard",
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
    "cancelled_on": None,
    "original_regn_no": "7",
    "extra_data": {}
}]

mock_search = fetchall_mock(search_data)
mock_search_not_found = fetchall_mock([])
mock_migration = fetchboth_mock(["50001"], ["50001"])
mock_retrieve = fetchboth_mock(all_queries_data, all_queries_data)
mock_cancellation = fetchboth_mock(['50001'], [['50001']])

class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **mock_search)
    def test_item_found(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_data, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **mock_search_not_found)
    def test_item_not_found(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_data, headers=headers)
        assert response.status_code == 404

    @mock.patch('psycopg2.connect')
    def test_search_not_json(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.post('/search', data=name_data, headers=headers)
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

    @mock.patch('psycopg2.connect', side_effect=Exception('Fail'))
    def test_database_failure(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/registration', data=valid_data, headers=headers)
        assert response.status_code == 500

    @mock.patch('psycopg2.connect', side_effect=Exception('Fail'))
    def test_database_failure_2(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_data, headers=headers)
        assert response.status_code == 500

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
        response = self.app.delete('/registration/50001')
        data = json.loads(response.data.decode('utf-8'))
        assert(data['cancelled'][0] == '50001')

    @mock.patch('psycopg2.connect', **mock_cancellation)
    @mock.patch('kombu.Producer.publish')
    def test_amendment(self, mc, kombu):
        response = self.app.put('/registration/50001', data=valid_data, headers={'Content-Type': 'application/json'})
        data = json.loads(response.data.decode('utf-8'))
        assert(data['new_registrations'][0] == 50002)
        assert(data['amended_registrations'][0] == '50001')

    @mock.patch('psycopg2.connect', **mock_search_not_found)
    def test_amendment_not_found(self, mc):
        response = self.app.put('/registration/50001', data=valid_data, headers={'Content-Type': 'application/json'})
        assert(response.status_code == 404)

    @mock.patch('psycopg2.connect', **mock_retrieve)
    def test_get_registration(self, mc):
        response = self.app.get("/registration/50000")
        data = json.loads(response.data.decode('utf-8'))
        assert data['debtor_name']['surname'] == 'Howard'

    @mock.patch('psycopg2.connect', **mock_retrieve)
    def test_get_migrated_registration(self, mc):
        response = self.app.get("/migrated_registration/500")
        data = json.loads(response.data.decode('utf-8'))
        print(data)
        assert data[0]['debtor_name']['surname'] == 'Howard'
