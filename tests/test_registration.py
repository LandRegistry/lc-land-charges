from unittest import mock
from application.routes import app
import os
import json


class MockConnection:
    def __init__(self, results):
        self.results = results

    def cursor(self):
        return MockCursor(self.results)

    def commit(self):
        pass

    def close(self):
        pass


class MockCursor:
    def __init__(self, results):
        self.results = results

    def execute(self, sql, dict):
        pass

    def close(self):
        pass

    def fetchall(self):
        return self.results

dir = os.path.dirname(__file__)
valid_data = open(os.path.join(dir, 'data/valid_data.json'), 'r').read()
mock_connection = MockConnection([valid_data])
mock_empty_connection = MockConnection([])

class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', return_value=mock_connection)
    def test_item_found(self, mock_connect):
        response = self.app.get('/search/222')
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', return_value=mock_empty_connection)
    def test_item_not_found(self, mock_connect):
        response = self.app.get('/search/222')
        assert response.status_code == 404

    @mock.patch('psycopg2.connect', return_value=mock_connection)
    def test_not_json(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.post('/register', data=valid_data, headers=headers)
        assert response.status_code == 415

    @mock.patch('psycopg2.connect', return_value=mock_connection)
    def test_new_registration(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/register', data=valid_data, headers=headers)
        assert response.status_code == 202

    @mock.patch('psycopg2.connect', side_effect=Exception('Fail'))
    def test_database_failure(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/register', data=valid_data, headers=headers)
        assert response.status_code == 500




#/register POST:
#Test new registration OK

