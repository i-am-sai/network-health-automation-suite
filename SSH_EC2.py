import paramiko

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


status = check_service_via_ssh(
    hostname="3.233.232.244",
    username="ubuntu",
    key_path="/home/sai/.ssh/network_health_key.pem",
    service_name="nginx"
)