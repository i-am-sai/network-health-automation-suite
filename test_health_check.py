import socket
import time
import dns.resolver
import requests
import pytest
import paramiko
import subprocess
import platform
import os
from utils import logger

URLS = [
"https://www.zappos.com"
]

# Hosts known to sit behind infrastructure that blocks ICMP (AWS ALB, some WAFs)
# PING_UNRELIABLE_HOSTS = ["www.ebooks.heart.org"]

# # CDN Hosted URLS:
# CDN_URLS = [
#     "https://www.zappos.com",
# ]



# HTTP request via requests
headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def get_hostname(url):
    hostname = url.replace("https://", "").replace("http://", "").split("/")[0]
    print(f"Verfying Hostname: {hostname}")
    return hostname

def ping_host(hostname, count=4):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, str(count), hostname]
    result = subprocess.run(command, capture_output=True, text=True, timeout=15)
    print(f"Ping output for {hostname}:\n{result.stdout}")
    return result

  

@pytest.mark.parametrize("url", URLS)
def test_dns_resolution(url):
    # DNS resolution
    logger.info("Test Case 1: DNS Resolution")  
    hostname = get_hostname(url)

    try:
        start = time.time()
        ip = socket.gethostbyname(hostname)
        dns_time =(time.time() - start) * 1000
        logger.info(f"DNS Resolved: {hostname} -> {ip} in ({dns_time:.2f} ms)")
    except socket.gaierror as e:
        pytest.fail(f"DNS resolution failed for {hostname}: {e}")
    
    assert ip is not None and len(ip) > 0, f"DNS failed to resolve {hostname}"


# @pytest.mark.parametrize("url", URLS)
# def test_ping_reachable(url):
#     hostname = get_hostname(url)
#     result = ping_host(hostname)

#     if hostname in URLS:
#         print(f"Note: {hostname} is ALB-fronted, ICMP is expected to fail regardless of health")
#         return  # informational only, no assertion
        
#     assert result.returncode == 0, f"{hostname} did not respond to ping (returncode {result.returncode})"

  
@pytest.mark.parametrize("url", URLS)
def test_cname(url):
    # CNAME chain + TTL via dnspython
    logger.info("Test Case 2: CNAME Chain and TTL")  
    hostname = get_hostname(url)
    try:
        answers = dns.resolver.resolve(hostname, "CNAME")
        for rdata in answers:
            logger.info(f"CNAME record: {rdata.target} (TTL: {answers.rrset.ttl}s)")
    except dns.resolver.NoAnswer:
        pytest.fail(f"CNAME: none (resolves directly, no CDN alias)")
    except Exception as e:
        pytest.fail(f"CNAME lookup skipped: {e}")

    assert answers is not None and len(answers) > 0, f"CNAME not found for {hostname}"

 
TCP_CONNECT_SLA_MS = 1000
@pytest.mark.parametrize("url", URLS)
def test_tcp_connect(url): 
    logger.info("Test Case 3: TCP Connect")   
    hostname = get_hostname(url)
    # Raw TCP connect timing
    try:
        ip = socket.gethostbyname(hostname)
        start = time.time()
        sock = socket.create_connection((ip, 443), timeout=5)
        tcp_time = (time.time() - start) * 1000
        sock.close()
        logger.info(f"TCP Connect: {ip}:443 in ({tcp_time:.2f} ms)")
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        pytest.fail(f"TCP connect FAILED: {e}")
    assert tcp_time < TCP_CONNECT_SLA_MS, (
        f"TCP connect to {hostname} took {tcp_time:.2f} ms, exceeds {TCP_CONNECT_SLA_MS} ms SLA"
    )

  
RESPONSE_TIME_SLA_MS = 5000
@pytest.mark.parametrize("url", URLS)
def test_http_request(url): 
    logger.info("Test Case 4: HTTP Request")  
    hostname = get_hostname(url)
    try:
        response = requests.get(url, timeout=10, headers=headers)
        http_time = response.elapsed.total_seconds() * 1000
        logger.info(f"HTTP response time: {http_time:.2f} ms")
        logger.info(f"HTTP Status Code: {response.status_code}")
        
        logger.info("Response Headers:")
        cache_control = response.headers.get("Cache-Control", "Not present")
        server_timing = response.headers.get("Server-Timing", "Not present")
        logger.info(f"Cache-Control: {cache_control}")
        logger.info(f"Server-Timing: {server_timing}")

    except requests.exceptions.RequestException as e:
        pytest.fail(f"HTTP request failed: {e}")

    assert response.status_code < 400, f"{url} returned {response.status_code}"
    assert http_time < RESPONSE_TIME_SLA_MS, (
        f"{url} took {http_time:.2f} ms, exceeds {RESPONSE_TIME_SLA_MS} ms SLA"
    )

def check_service_via_ssh(hostname, username, key_path, service_name):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, username=username, key_filename=key_path, timeout=10)

        command = f"systemctl is-active {service_name}"
        stdin, stdout, stderr = client.exec_command(command)

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        print(f"Service '{service_name}' status: {output}")
        if error:
            print(f"stderr: {error}")

        return output

    finally:
        client.close()

KEY_PATH = "ec2_key.pem"
   
@pytest.mark.parametrize("hostname,username,key_path,service_name", [
    ("13.220.16.210", "ubuntu", "ec2_key.pem", "nginx")
])
def test_nginx_service_running(hostname, username, key_path, service_name):
    logger.info("Test Case 5: SSH Service Check") 

    status = check_service_via_ssh(
        hostname=hostname,
        username=username,
        key_path=key_path,
        service_name=service_name
    )
    logger.info("nginx service status: %s", status)    

    assert status == "active", (
        f"{service_name} is not active, status: {status}"
    )




# CDN_URLS = [
#     "https://www.zappos.com",
# ]

# @pytest.mark.parametrize("url", CDN_URLS)
# def test_cache_header_present_on_cdn_sites(url):
#     response = requests.get(url, timeout=10, headers=HEADERS)
#     cache_control = response.headers.get("Cache-Control")
#     server_timing = response.headers.get("Server-Timing")
#     assert cache_control is not None or server_timing is not None, (
#         f"{url} is expected to be CDN-backed but has no cache headers"
#     )



print("=" * 60)
print()
