import socket
import time

host = "www.github.com"
port = 443 #https connection

start = time.time()
ip = socket.gethostbyname(host)
dns_time = time.time() - start

start = time.time()
sock = socket.create_connection((ip, port), timeout=5)
connect_time = time.time() - start  
sock.close()

print(f"Resolved {host} -> {ip}")
print(f"DNS time: {dns_time} seconds")
print(f"DNS Lookup time: {dns_time*1000:.2f} ms")
print(f"TCP connect time: {connect_time*1000:.2f} ms")
# print(f"Local address/port: {sock.getsockname()}")
# print(f"Remote address/port: {sock.getpeername()}")

