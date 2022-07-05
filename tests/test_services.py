import pytest

from passtry import jobs


def test_ssh(ssh_service):
    service_host, service_port = ssh_service
    job = jobs.Job()
    tasks = [
        ('ssh', 'user', 'Password', service_host, service_port, None),
        ('ssh', 'user', 'P@55w0rd!', service_host, service_port, None),
    ]
    job.start(tasks)
    assert job.output() == [f'ssh://user:P@55w0rd!@{service_host}:{service_port}']


def test_ftp(ftp_service):
    service_host, service_port = ftp_service
    job = jobs.Job()
    tasks = [
        ('ftp', 'user', 'Password', service_host, service_port, None),
        ('ftp', 'user', 'P@55w0rd!', service_host, service_port, None),
    ]
    job.start(tasks)
    assert job.output() == [f'ftp://user:P@55w0rd!@{service_host}:{service_port}']


def test_http_basic(http_service):
    service_host, service_port = http_service
    job = jobs.Job()
    tasks = [
        ('http-basic', 'user', 'Password', service_host, service_port, {'path': '/http-basic/'}),
        ('http-basic', 'user', 'P@55w0rd!', service_host, service_port, {'path': '/http-basic/'}),
    ]
    job.start(tasks)
    assert job.output() == [f"http-basic://user:P@55w0rd!@{service_host}:{service_port} -- {{'path': '/http-basic/'}}"]


def test_https_basic(https_service):
    service_host, service_port = https_service
    job = jobs.Job()
    tasks = [
        ('https-basic', 'user', 'Password', service_host, service_port, {'path': '/http-basic/'}),
        ('https-basic', 'user', 'P@55w0rd!', service_host, service_port, {'path': '/http-basic/'}),
    ]
    job.start(tasks)
    assert job.output() == [f"https-basic://user:P@55w0rd!@{service_host}:{service_port} -- {{'path': '/http-basic/'}}"]
