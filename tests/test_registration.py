from unittest import mock
from application.routes import app
import os
import json


class MockConnection:
    def __init__(self, results):
        self.results = results

    def cursor(self):
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

dir = os.path.dirname(__file__)
valid_data = open(os.path.join(dir, 'data/valid_data.json'), 'r').read()
name_data = '{"forenames": "Bob Oscar Francis", "surname": "Howard"}'
mock_connection = MockConnection([valid_data])
mock_empty_connection = MockConnection([])
mock_insert_connection = MockConnection(["50001", "50002"])

class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', return_value=mock_connection)
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