# When you write automation scripts:

# Private IP — device on local network
host = "192.168.1.1"

# Loopback — your own machine
host = "127.0.0.1"

# CIDR — you'll see this in AWS security group rules
# "allow traffic from 192.168.1.0/24" 
# means allow anyone from 192.168.1.1 to 192.168.1.254

# Public IP — external server on internet
host = "8.8.8.8"    # Google's public DNS server

