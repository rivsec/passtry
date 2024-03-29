import pathlib
import os
import shutil
import socket
import tempfile

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


@pytest.fixture(scope='session')
def ftp_service(docker_ip, docker_services):
    docker_port = docker_services.port_for('debian-latest-vsftpd', 21)
    docker_services.wait_until_responsive(check=lambda: socket_available(docker_ip, docker_port), timeout=30, pause=1)
    return docker_ip, docker_port


@pytest.fixture(scope='session')
def http_service(docker_ip, docker_services):
    docker_port = docker_services.port_for('nginx-latest', 80)
    docker_services.wait_until_responsive(check=lambda: socket_available(docker_ip, docker_port), timeout=30, pause=1)
    return docker_ip, docker_port


@pytest.fixture(scope='session')
def https_service(docker_ip, docker_services):
    docker_port = docker_services.port_for('nginx-latest', 443)
    docker_services.wait_until_responsive(check=lambda: socket_available(docker_ip, docker_port), timeout=30, pause=1)
    return docker_ip, docker_port


@pytest.fixture(scope='session')
def data_dir():
    cwd = pathlib.Path(os.getenv('PYTEST_CURRENT_TEST').split('::')[0]).parent
    return cwd / 'data'


@pytest.fixture(scope='function')
def tmp_dir():
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)
