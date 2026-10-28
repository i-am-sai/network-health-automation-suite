import subprocess
import platform
import pytest
import socket
import time
from utils.logger import logger
from utils.report import test_results, record_result
import dns.resolver
import requests
import ssl
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
def get_hostname(url):
    hostname = url.replace("https://", "").replace("http://", "").split("/")[0]
    print(f"Verfying Hostname: {hostname}")
    return hostname


URLS = [
    "www.google.com"
]

headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }


def get_tls_certificate_details(hostname, port=443):
    context = ssl.create_default_context()

    with socket.create_connection((hostname, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:

            certificate = tls_sock.getpeercert()

            details = {
                "subject": certificate.get("subject"),
                "issuer": certificate.get("issuer"),
                "version": certificate.get("version"),
                "serial_number": certificate.get("serialNumber"),
                "not_before": certificate.get("notBefore"),
                "not_after": certificate.get("notAfter"),
                "tls_version": tls_sock.version(),
                "cipher": tls_sock.cipher(),
            }

            return details

# @pytest.mark.dev
# def test_ssl_certificate():
#     logger.info("Test Case 4: SSL Certificate Validation")

#     try:
#         start = time.time()

#         details = get_tls_certificate_details(
#             SSH_HOST,
#             TLS_PORT
#         )

#         tls_time = (time.time() - start) * 1000

#         logger.info(f"Certificate Issuer: {details['issuer']}")
#         logger.info(f"Certificate Subject: {details['subject']}")
#         logger.info(f"Certificate Version: {details['version']}")
#         logger.info(f"Serial Number: {details['serial_number']}")
#         logger.info(f"Valid From: {details['not_before']}")
#         logger.info(f"Valid Until: {details['not_after']}")
#         logger.info(f"TLS Version: {details['tls_version']}")
#         logger.info(f"Cipher: {details['cipher']}")

#         result = record_result(
#             "test_ssl_certificate",
#             f"{SSH_HOST}:{TLS_PORT}",
#             "passed",
#             tls_time,
#             details
#         )
#         print(result)

#         # Assertions
#         assert details["issuer"], "Certificate issuer is missing"
#         assert details["subject"], "Certificate subject is missing"
#         assert details["not_after"], "Certificate expiry date is missing"

#         assert details["tls_version"] in (
#             "TLSv1.2",
#             "TLSv1.3"
#         ), f"Unsupported TLS version: {details['tls_version']}"

#     except Exception as e:

#         result = record_result(
#             "test_ssl_certificate",
#             f"{SSH_HOST}:{TLS_PORT}",
#             "failed",
#             0,
#             {"error": str(e)}
#         )
#         print(result)
        

#         pytest.fail(f"SSL certificate validation failed: {e}")