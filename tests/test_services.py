import pytest

from passtry import jobs


def test_ssh_connection(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job()
    tasks = [
        ('ssh', 'user', 'Password', ssh_host, ssh_port),
        ('ssh', 'user', 'P@55w0rd!', ssh_host, ssh_port),
    ]
    job.start(tasks)
    assert job.output() == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_ftp_connection(ftp_service):
    ftp_host, ftp_port = ftp_service
    job = jobs.Job()
    tasks = [
        ('ftp', 'user', 'Password', ftp_host, ftp_port),
        ('ftp', 'user', 'P@55w0rd!', ftp_host, ftp_port),
    ]
    job.start(tasks)
    assert job.output() == [f'ftp://user:P@55w0rd!@{ftp_host}:{ftp_port}']
