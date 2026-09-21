import socket

# This is exactly what happens under the hood
# # when you connect to any server

# sock = socket.socket()
# sock.connect(("192.168.1.1", 22))    # IP + Port together
# OS automatically assigns ephemeral port on your side


host = "ebooks.heart.org"
ip = socket.gethostbyname(host)
print("IP: ", ip)

import requests
response = requests.get(f"https://{host}")
print(response.status_code) # 200
print(response.headers) # response headers