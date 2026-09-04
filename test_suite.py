import socket
import pytest
import requests

URLS = [
    "https://www.ebooks.heart.org",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

RESPONSE_TIME_SLA_MS = 2000


def get_hostname(url):
    return url.replace("https://", "").replace("http://", "").split("/")[0]


@pytest.mark.parametrize("url", URLS)
def test_dns_resolves(url):
    hostname = get_hostname(url)
    ip = socket.gethostbyname(hostname)
    assert ip is not None and len(ip) > 0, f"DNS failed to resolve {hostname}"


@pytest.mark.parametrize("url", URLS)
def test_http_status(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    assert response.status_code < 400, f"{url} returned {response.status_code}"


@pytest.mark.parametrize("url", URLS)
def test_response_time_sla(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    elapsed_ms = response.elapsed.total_seconds() * 1000
    assert elapsed_ms < RESPONSE_TIME_SLA_MS, (
        f"{url} took {elapsed_ms:.2f} ms, exceeds {RESPONSE_TIME_SLA_MS} ms SLA"
    )


@pytest.mark.parametrize("url", URLS)
def test_cache_header_present(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    cache_control = response.headers.get("Cache-Control")
    server_timing = response.headers.get("Server-Timing")
    assert cache_control is not None or server_timing is not None, (
        f"{url} has no Cache-Control or Server-Timing header"
    )