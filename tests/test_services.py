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
