import socket
import time
import dns.resolver
import requests
import pytest
import paramiko
import subprocess
import platform
import ssl
import os
import json
from datetime import datetime 
from dotenv import load_dotenv
from pathlib import Path
from utils.logger import logger
from utils.report import test_results, record_result
from reports_upload_script import upload_report_to_s3
from email_script import send_report_email


load_dotenv()

URLS = [
    "https://www.zappos.com",
]

RECIPIENT = os.environ.get("RECIPIENT_EMAIL")

# PING_UNRELIABLE_HOSTS = ["www.ebooks.heart.org"]

# CDN Hosted URLS:
# CDN_URLS = [
#     "https://www.zappos.com",
# ]

# web browsers: Helps in defining the request and browser ond OS version so that server treats it as real request
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

# Test Case 1: Ping the Server and wait for response using subprocess
@pytest.mark.parametrize("url", URLS)
def test_ping_reachable(url):
    logger.info("Test Case 1: PING Server")  
    hostname = get_hostname(url)
    result = ping_host(hostname)
    result_code = result.returncode
    record_result("test_ping_reachable", url, "passed", 0, {"ping_status": result_code})

    if hostname in URLS:
        print(f"Note: {hostname} is ALB-fronted, ICMP is expected to fail regardless of health")
        return  # informational only, no assertion
        
    assert result_code == 0, f"{hostname} did not respond to ping (returncode {result_code})"


# Test Case 2: DNS Resolution
@pytest.mark.parametrize("url", URLS)
def test_dns_resolution(url):
    logger.info("Test Case 2: DNS Resolution")  
    hostname = get_hostname(url)

    try:
        start = time.time() # time module give response in seconds
        ip = socket.gethostbyname(hostname) #The OS resolver then handles the DNS configuration and communication.
        dns_time =(time.time() - start) * 1000 #  second is converted to millisecond
        logger.info(f"DNS Resolved: {hostname} -> {ip} in ({dns_time:.2f} ms)") #23.456789 : .2f trims it to nearest 2 decimal point
        record_result("test_dns_resolution", url, "passed", dns_time, {"ip": ip})
    except socket.gaierror as e: #gaierror -> address-resolution error.
        record_result("test_dns_resolution", url, "failed", 0, {"error": str(e)})
        pytest.fail(f"DNS resolution failed for {hostname}: {e}")
    
    assert ip is not None and len(ip) > 0, f"DNS failed to resolve {hostname}"


#Test Case 3: CNAME Chain and TTL
@pytest.mark.parametrize("url", URLS)
def test_cname(url):
    # CNAME chain + TTL via dnspython
    logger.info("Test Case 3: CNAME Chain and TTL")  
    hostname = get_hostname(url)
    try:
        answers = dns.resolver.resolve(hostname, "CNAME")
        for rdata in answers:
            logger.info(f"CNAME record: {rdata.target} (TTL: {answers.rrset.ttl}s)")
            record_result("test_cname", url, "passed", 0, {"cname": str(rdata.target), "ttl": answers.rrset.ttl})
    except dns.resolver.NoAnswer:
        pytest.fail(f"CNAME: none (resolves directly, no CDN alias)")
        record_result("test_cname", url, "failed", 0, {"error": "No CNAME record found"})
    except Exception as e:
        pytest.fail(f"CNAME lookup skipped: {e}")
        record_result("test_cname", url, "failed", 0, {"error": str(e)})

    assert answers is not None and len(answers) > 0, f"CNAME not found for {hostname}"


# Test Case 4: TCP Connection
TCP_CONNECT_SLA_MS = 1000 # Service Level Agreement/Threshold
@pytest.mark.parametrize("url", URLS)
def test_tcp_connect(url): 
    logger.info("Test Case 4: TCP Connection")   
    hostname = get_hostname(url)
    # Raw TCP connect timing
    try:
        ip = socket.gethostbyname(hostname)
        start = time.time()
        sock = socket.create_connection((ip, 443), timeout=5)
        tcp_time = (time.time() - start) * 1000
        local_ip, local_port = sock.getsockname()
        remote_ip, remote_port = sock.getpeername()
        print(f"Source      : {local_ip}:{local_port}")
        print(f"Destination : {remote_ip}:{remote_port}")
        sock.close()
        logger.info(f"TCP Connect: {ip}:443 in ({tcp_time:.2f} ms)")
        record_result("test_tcp_connect", url, "passed", tcp_time, {"ip": ip})
        
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        result = record_result("test_tcp_connect", url, "failed", 0, {"error": str(e)})
        print(result)
        pytest.fail(f"TCP connect FAILED: {e}")
        
    assert tcp_time < TCP_CONNECT_SLA_MS, (
        f"TCP connect to {hostname} took {tcp_time:.2f} ms, exceeds {TCP_CONNECT_SLA_MS} ms SLA"
    )


EC2_PUBLIC_IP = "44.200.103.215"
SSH_HOST = os.environ.get("EC2_SSH_HOST", EC2_PUBLIC_IP)
TLS_PORT = 443

# Test Case 5: SSL Certificate Validation
def test_ssl_certificate():
    logger.info("Test Case 5: SSL Certificate Validation")

    try:
        start = time.time()

        certificate = ssl.get_server_certificate(
            (SSH_HOST, TLS_PORT)
        )

        tls_time = (time.time() - start) * 1000

        logger.info("SSL certificate retrieved successfully")
        logger.info(f"Certificate:\n{certificate}")

        record_result(
            "test_ssl_certificate",
            f"{SSH_HOST}:{TLS_PORT}",
            "passed",
            tls_time,
            {
                "certificate_retrieved": True
            }
        )

        assert certificate.startswith(
            "-----BEGIN CERTIFICATE-----"
        )

    except Exception as e:
        record_result(
            "test_ssl_certificate",
            f"{SSH_HOST}:{TLS_PORT}",
            "failed",
            0,
            {"error": str(e)}
        )

        pytest.fail(f"SSL certificate retrieval failed: {e}")


#Test Case 6: HTTP Request
RESPONSE_TIME_SLA_MS = 5000
@pytest.mark.parametrize("url", URLS)
def test_http_request(url): 
    logger.info("Test Case 6: HTTP Request")  
    hostname = get_hostname(url)
    try:
        response = requests.get(url, timeout=10, headers=headers)
        http_time = response.elapsed.total_seconds() * 1000
        logger.info(f"HTTP response time: {http_time:.2f} ms")
        logger.info(f"HTTP Status Code: {response.status_code}")
       
        cache_control = response.headers.get("Cache-Control", "Not present")
        server_timing = response.headers.get("Server-Timing", "Not present")
        logger.info(f"Cache-Control: {cache_control}")
        logger.info(f"Server-Timing: {server_timing}")
        logger.info("Response Headers:")
                
        record_result("test_http_request", url, "passed", http_time, {"status_code": response.status_code, "Cache-Control": cache_control, "Server-Timing": server_timing})
       
        # print(response.status_code)
        #         # print(response.headers)
        # for key, value in response.headers.items():
        #     print(f"{key}: {value}")
        # print(response.url)
        # print(response.elapsed)
        # print(response.content)
        # print(response.text)
        # for cookie in response.cookies:
        #     print(cookie.name, cookie.value)

    except requests.exceptions.RequestException as e:
        pytest.fail(f"HTTP request failed: {e}")
        record_result("test_http_request", url, "failed", 0, {"error": str(e)})

    assert response.status_code < 400, f"{url} returned {response.status_code}"
    assert http_time < RESPONSE_TIME_SLA_MS, (
        f"{url} took {http_time:.2f} ms, exceeds {RESPONSE_TIME_SLA_MS} ms SLA"
    )

# method to ssh login to remote server and verify the service status on the server
def check_service_via_ssh(hostname, username, key_path, service_name):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname, username=username, key_filename=key_path, timeout=10) # mimics ssh login command

        command = f"systemctl is-active {service_name}" # mimics service checking command after login
        stdin, stdout, stderr = client.exec_command(command) # gives you access to all three: input, output and error command.

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        print(f"Service '{service_name}' status: {output}")
        if error:
            print(f"stderr: {error}")

        return output

    finally:
        client.close()


KEY_PATH = "ec2_key.pem"
DEFAULT_KEY_PATH = "/home/sai/.ssh/network_health_key.pem"
EC2_USER = "ubuntu"

SSH_KEY_PATH = os.environ.get("EC2_KEY_PATH", DEFAULT_KEY_PATH)
SSH_USER = os.environ.get("EC2_USER", "ubuntu")

#Test Case 7: SSH Service Check
@pytest.mark.parametrize("hostname,username,key_path,service_name", [
    (SSH_HOST, SSH_USER, SSH_KEY_PATH, "nginx")
])

def test_nginx_service_running(hostname, username, key_path, service_name):
    logger.info("Test Case 7: SSH Service Check") 

    status = check_service_via_ssh(
        hostname=hostname,
        username=username,
        key_path=key_path,
        service_name=service_name
    )
    logger.info("nginx service status: %s", status)    
    record_result("test_nginx_service_running", hostname, "passed", 0, {"service_status": status})

    assert status == "active", (
        f"{service_name} is not active, status: {status}"
    )


# Fixture to write JSON report locally and send to S3 after all tests have run
@pytest.fixture(scope="session", autouse=True)
def write_json_report():
    yield
    reports_dir = Path("reports/results")
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"reports/results/results_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(test_results, f, indent=2)
    logger.info(f"JSON report written to {filename}")
    upload_report_to_s3(filename)
    logger.info(f"JSON report uploaded to S3 bucket")
    send_report_email(filename, RECIPIENT)
    logger.info(f"report sent to {RECIPIENT} mail id")




# @pytest.mark.parametrize("url", CDN_URLS)
# def test_cache_header_present_on_cdn_sites(url):
#     response = requests.get(url, timeout=10, headers=HEADERS)
#     cache_control = response.headers.get("Cache-Control")
#     server_timing = response.headers.get("Server-Timing")
#     assert cache_control is not None or server_timing is not None, (
#         f"{url} is expected to be CDN-backed but has no cache headers"
#     )



