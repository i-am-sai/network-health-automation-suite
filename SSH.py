import paramiko

# Create SSH client
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Connect using key based auth
client.connect(
    hostname="192.168.1.1",
    username="admin",
    key_filename="~/.ssh/id_rsa"
)

# Run commands remotely
stdin, stdout, stderr = client.exec_command("show interfaces")
output = stdout.read().decode()
print(output)

client.close()

#Your Python script just SSHed into a network device, ran a command, and captured the output — automatically, 
# without human interaction. That's network automation.