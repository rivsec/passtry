import socket

import pytest


def socket_available(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ip, port))
    except socket.error:
        return False
    else:
        return True


@pytest.fixture(scope='session')
def ssh_service(docker_ip, docker_services):
    docker_port = docker_services.port_for('debian-latest-openssh', 22)
    docker_services.wait_until_responsive(check=lambda: socket_available(docker_ip, docker_port), timeout=30, pause=1)
    return docker_ip, docker_port
