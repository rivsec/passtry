import pytest

from passtry import jobs


def test_ssh(ssh_service):
    service_host, service_port = ssh_service
    job = jobs.Job(watch_failures=False)
    job.start(
        [f'ssh:{service_port}'], [service_host], ['user'], ['P@55w0rd!', 'Password']
    )
    assert job.output() == [f'ssh://user:P@55w0rd!@{service_host}:{service_port}']


def test_ftp(ftp_service):
    service_host, service_port = ftp_service
    job = jobs.Job(watch_failures=False)
    job.start(
        [f'ftp:{service_port}'], [service_host], ['user'], ['P@55w0rd!', 'Password']
    )
    assert job.output() == [f'ftp://user:P@55w0rd!@{service_host}:{service_port}']


def test_http_basic(http_service):
    service_host, service_port = http_service
    job = jobs.Job(watch_failures=False)
    job.start(
        [f'http-basic:{service_port}'], [service_host], ['user'], ['P@55w0rd!', 'Password'], {'http-basic': {'path': '/http-basic/'}}
    )
    assert job.output() == [f'http://user:P@55w0rd!@{service_host}:{service_port}/http-basic/']


def test_https_basic(https_service):
    service_host, service_port = https_service
    job = jobs.Job(watch_failures=False)
    job.start(
        [f'https-basic:{service_port}'], [service_host], ['user'], ['P@55w0rd!', 'Password'], {'https-basic': {'path': '/http-basic/'}}
    )
    assert job.output() == [f'https://user:P@55w0rd!@{service_host}:{service_port}/http-basic/']
