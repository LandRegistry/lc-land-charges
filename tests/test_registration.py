from unittest import mock
from application.routes import app
import os
import json
import datetime


class MockConnection:
    def __init__(self, results):
        self.results = results

    def cursor(self, cursor_factory=None):
        return MockCursor(self.results, self)

    def commit(self):
        pass

    def close(self):
        pass


class MockCursor:
    def __init__(self, results, conn):
        self.results = results
        self.connection = conn

    def execute(self, sql, dict):
        pass

    def close(self):
        pass

    def fetchall(self):
        return self.results

    def fetchone(self):
        return [1]

directory = os.path.dirname(__file__)
valid_data = open(os.path.join(directory, 'data/valid_data.json'), 'r').read()
migration_data = open(os.path.join(directory, 'data/migrator.json'), 'r').read()
name_data = '{"forenames": "Bob Oscar Francis", "surname": "Howard"}'
mock_connection = MockConnection([valid_data])
mock_empty_connection = MockConnection([])
mock_insert_connection = MockConnection(["50001", "50002"])
mock_migrate_connection = MockConnection(["50001"])
mock_query_connection = MockConnection([{"registration_no": "50000", "registration_date": "2012-08-09",
                                         "application_type": "PAB", "id": "56", "debtor_reg_name_id": "12",
                                         "forename": "Bob", "register_id": "2",
                                         "middle_names": "Oscar Francis",
                                         "surname": "Howard",
                                         "occupation": "Civil Servant",
                                         "trading_name": "Bob",
                                         "application_reference": "123456789",
                                         "line_1": "123 The Street",
                                         "line_2": "Somewhere",
                                         "line_3": "",
                                         "line_4": "",
                                         "line_5": "",
                                         "line_6": "",
                                         "original_regn_no": "7",
                                         "extra_data": {}}])

search_data = [{"register_detl_id": 1, "registration_date": datetime.date(2005, 12, 2), "application_type": "PAB",
                "registration_no": "50135"}]
mock_search_connection = MockConnection(search_data)

class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', return_value=mock_search_connection)
    def test_item_found(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_data, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', return_value=mock_empty_connection)
    def test_item_not_found(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_data, headers=headers)
        assert response.status_code == 404

    @mock.patch('psycopg2.connect', return_value=mock_connection)
    def test_search_not_json(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.post('/search', data=name_data, headers=headers)
        assert response.status_code == 415

    @mock.patch('psycopg2.connect', return_value=mock_connection)
    def test_not_json(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.post('/register', data=valid_data, headers=headers)
        assert response.status_code == 415

    @mock.patch('psycopg2.connect', return_value=mock_insert_connection)
    @mock.patch('kombu.Producer.publish')
    def test_new_registration(self, mock_connect, mock_publish):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/register', data=valid_data, headers=headers)
        assert response.status_code == 200
        assert mock_publish.called

    @mock.patch('psycopg2.connect', side_effect=Exception('Fail'))
    def test_database_failure(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/register', data=valid_data, headers=headers)
        assert response.status_code == 500

    @mock.patch('psycopg2.connect', side_effect=Exception('Fail'))
    def test_database_failure_2(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=name_data, headers=headers)
        assert response.status_code == 500

    @mock.patch('psycopg2.connect', return_value=mock_migrate_connection)
    def test_migration_success(self, mc):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/migrated_record', data=migration_data, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', return_value=mock_migrate_connection)
    def test_migration_invalid(self, mc):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/migrated_record', data='{"cheese": "brie"}', headers=headers)
        assert response.status_code == 400

    @mock.patch('psycopg2.connect', return_value=mock_query_connection)
    def test_get_registration(self, mc):
        response = self.app.get("/registration/50000")
        data = json.loads(response.data.decode('utf-8'))
        assert data['debtor_name']['surname'] == 'Howard'
        # TODO: test several other fields