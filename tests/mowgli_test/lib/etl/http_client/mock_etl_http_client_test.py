import pytest

from tests.mowgli_test.lib.etl.http_client.mock_etl_http_client import MockEtlHttpClient


def test_mock_http_client():
    client = MockEtlHttpClient()
    test_url = "http://example.com"
    test_content = "this\nis\ntest\ncontent"
    client.add_mock_response(test_url, test_content)
    url_contents = client.urlopen(test_url)
    assert url_contents.read() == test_content


def test_unconfigd_mock_http_client():
    client = MockEtlHttpClient()
    with pytest.raises(AssertionError):
        client.urlopen("http://example.com")
