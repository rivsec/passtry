import pytest

from passtry import jobs


def test_ssh_connection(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job()
    tasks = [
        ('ssh', 'user', 'Password', ssh_host, ssh_port),
        ('ssh', 'user', 'P@55w0rd!', ssh_host, ssh_port),
    ]
    job.consume(tasks)
    job.start()
    output = [job.prettify(result) for result in job.results if result]
    assert output == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']
