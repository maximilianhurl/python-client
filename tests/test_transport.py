# coding: utf-8
from coreapi import get_session, get_default_session, Link
from coreapi.exceptions import TransportError
from coreapi.transport import HTTPTransport
import pytest
import requests


@pytest.fixture
def http():
    return HTTPTransport()


class MockResponse(object):
    def __init__(self, content):
        self.content = content
        self.headers = {}
        self.url = 'http://example.org'


# Test transport errors.

def test_unknown_scheme():
    session = get_default_session()
    with pytest.raises(TransportError):
        session.determine_transport('ftp://example.org')


def test_missing_scheme():
    session = get_default_session()
    with pytest.raises(TransportError):
        session.determine_transport('example.org')


def test_missing_hostname():
    session = get_default_session()
    with pytest.raises(TransportError):
        session.determine_transport('http://')


# Test basic transition types.

def test_get(monkeypatch, http):
    def mockreturn(method, url, headers):
        return MockResponse(b'{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    link = Link(url='http://example.org', action='get')
    doc = http.transition(link)
    assert doc == {'example': 123}


def test_get_with_parameters(monkeypatch, http):
    def mockreturn(method, url, params, headers):
        insert = params['example'].encode('utf-8')
        return MockResponse(
            b'{"_type": "document", "example": "' + insert + b'"}'
        )

    monkeypatch.setattr(requests, 'request', mockreturn)

    link = Link(url='http://example.org', action='get')
    doc = http.transition(link, params={'example': 'abc'})
    assert doc == {'example': 'abc'}


def test_post(monkeypatch, http):
    def mockreturn(method, url, data, headers):
        insert = data.encode('utf-8')
        return MockResponse(b'{"_type": "document", "data": ' + insert + b'}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    link = Link(url='http://example.org', action='post')
    doc = http.transition(link, params={'example': 'abc'})
    assert doc == {'data': {'example': 'abc'}}


def test_delete(monkeypatch, http):
    def mockreturn(method, url, headers):
        return MockResponse(b'')

    monkeypatch.setattr(requests, 'request', mockreturn)

    link = Link(url='http://example.org', action='delete')
    doc = http.transition(link)
    assert doc is None


# Test credentials

def test_credentials(monkeypatch):
    def mockreturn(method, url, headers):
        return MockResponse(headers.get('authorization', ''))

    monkeypatch.setattr(requests, 'request', mockreturn)

    credentials = {'example.org': 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='}
    session = get_session(credentials=credentials)
    transport = session.transports[0]

    # Requests to example.org include credentials.
    response = transport.make_http_request(session, 'http://example.org/123')
    assert response.content == 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='

    # Requests to other.org do not include credentials.
    response = transport.make_http_request(session, 'http://other.org/123')
    assert response.content == ''


# Test custom headers

def test_headers(monkeypatch):
    def mockreturn(method, url, headers):
        return MockResponse(headers.get('User-Agent', ''))

    monkeypatch.setattr(requests, 'request', mockreturn)

    headers = {'User-Agent': 'Example v1.0'}
    session = get_session(headers=headers)
    transport = session.transports[0]

    # Requests include custom headers.
    response = transport.make_http_request(session, 'http://example.org/123')
    assert response.content == 'Example v1.0'
