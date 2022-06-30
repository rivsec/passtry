import pytest

from passtry import (
    exceptions,
    logs,
    jobs,
)


def test_combining_lists():
    job = jobs.Job()
    targets = ('example.com', 'ssh.example.com')
    usernames = ('root', 'guest')
    passwords = ('Password', 'Passw0rd')
    ports = (22, 8222)
    services = ('ssh',)
    assert job.combine(services, usernames, passwords, targets, ports) == [
        ['ssh', 'root', 'Password', 'example.com', 22],
        ['ssh', 'root', 'Password', 'example.com', 8222],
        ['ssh', 'root', 'Password', 'ssh.example.com', 22],
        ['ssh', 'root', 'Password', 'ssh.example.com', 8222],
        ['ssh', 'root', 'Passw0rd', 'example.com', 22],
        ['ssh', 'root', 'Passw0rd', 'example.com', 8222],
        ['ssh', 'root', 'Passw0rd', 'ssh.example.com', 22],
        ['ssh', 'root', 'Passw0rd', 'ssh.example.com', 8222],
        ['ssh', 'guest', 'Password', 'example.com', 22],
        ['ssh', 'guest', 'Password', 'example.com', 8222],
        ['ssh', 'guest', 'Password', 'ssh.example.com', 22],
        ['ssh', 'guest', 'Password', 'ssh.example.com', 8222],
        ['ssh', 'guest', 'Passw0rd', 'example.com', 22],
        ['ssh', 'guest', 'Passw0rd', 'example.com', 8222],
        ['ssh', 'guest', 'Passw0rd', 'ssh.example.com', 22],
        ['ssh', 'guest', 'Passw0rd', 'ssh.example.com', 8222],
    ]


def test_combining_lists_empty():
    job = jobs.Job()
    targets = ('example.com', 'ssh.example.com')
    usernames = ('root', 'guest')
    passwords = None
    ports = (22, 8222)
    services = ('ssh',)
    assert job.combine(services, usernames, passwords, targets, ports) == [
        ['ssh', 'root', None, 'example.com', 22],
        ['ssh', 'root', None, 'example.com', 8222],
        ['ssh', 'root', None, 'ssh.example.com', 22],
        ['ssh', 'root', None, 'ssh.example.com', 8222],
        ['ssh', 'guest', None, 'example.com', 22],
        ['ssh', 'guest', None, 'example.com', 8222],
        ['ssh', 'guest', None, 'ssh.example.com', 22],
        ['ssh', 'guest', None, 'ssh.example.com', 8222],
    ]


def test_uri_split_exclusive_services_ports():
    """Port numbers cannot be declared if more than one service is tested"""
    with pytest.raises(exceptions.ConfigurationError):
        jobs.Job().split('ssh+ftp://admin:password@example.com:22')


def test_uri_split_service_doesnt_exist():
    with pytest.raises(exceptions.ConfigurationError):
        jobs.Job().split('hXXp://example.com')


def test_uri_split_set_port():
    job = jobs.Job()
    assert job.split('ssh://admin:password@example.com:22') == [
        ['ssh'], ['admin'], ['password'], ['example.com'], [22]
    ]
    assert job.split('ssh://admin:password@example.com:2222') == [
        ['ssh'], ['admin'], ['password'], ['example.com'], [2222]
    ]


def test_uri_split_no_default_port():
    job = jobs.Job()
    assert job.split('http://example.com') == [
        ['http'], None, None, ['example.com'], None
    ]


def test_uri_split_override_port():
    job = jobs.Job()
    assert job.split('http://example.com:81') == [
        ['http'], None, None, ['example.com'], [81],
    ]


def test_uri_split_multiple_services():
    job = jobs.Job()
    assert job.split('ssh+ftp://admin:password@example.com') == [
        ['ssh', 'ftp'], ['admin'], ['password'], ['example.com'], None
    ]


def test_uri_split_plus_in_passwords():
    job = jobs.Job()
    result = job.split('ssh://admin:password+\'pass+word2\'+"password+3"@example.com')
    assert job.split('ssh://admin:password+\'pass+word2\'+"password+3"@example.com') == [
        ['ssh'], ['admin'], ['password', 'pass+word2', 'password+3'], ['example.com'], None
    ]


def test_uri_split_no_username():
    job = jobs.Job()
    assert job.split('ssh+ftp://:password@example.com') == [
        ['ssh', 'ftp'], None, ['password'], ['example.com'], None
    ]


def test_uri_split_no_password():
    job = jobs.Job()
    assert job.split('ssh+ftp://admin@example.com') == [
        ['ssh', 'ftp'], ['admin'], None, ['example.com'], None
    ]


def test_uri_split_multiple_targets():
    job = jobs.Job()
    assert job.split('ssh+ftp://admin+root+user:password+Passw0rd@example.com+other.example.com') == [
        ['ssh', 'ftp'], ['admin', 'root', 'user'], ['password', 'Passw0rd'], ['example.com', 'other.example.com'], None
    ]


def test_max_failed_no_results(ssh_service):
    ssh_host, ssh_port = ssh_service
    tasks = [
        ('ssh', 'user', 'Password', ssh_host, 9991),
        ('ssh', 'user', 'Password', ssh_host, 9992),
        ('ssh', 'user', 'Password', ssh_host, 9993),
        ('ssh', 'user', 'Password', ssh_host, 9994),
        ('ssh', 'user', 'Password', ssh_host, 9995),
        ('ssh', 'user', 'P@55w0rd!', ssh_host, ssh_port),
    ]
    job = jobs.Job(failed_number=3)
    job.start(tasks)
    assert job.failures.get() == 3
    assert job.results.get() == list()


def test_max_failed_disable_failures(ssh_service):
    ssh_host, ssh_port = ssh_service
    tasks = [
        ('ssh', 'user', 'Password', ssh_host, 9991),
        ('ssh', 'user', 'Password', ssh_host, 9992),
        ('ssh', 'user', 'Password', ssh_host, 9993),
        ('ssh', 'user', 'Password', ssh_host, 9994),
        ('ssh', 'user', 'Password', ssh_host, 9995),
        ('ssh', 'user', 'P@55w0rd!', ssh_host, ssh_port),
    ]
    job = jobs.Job(failed_number=3, watch_failures=False)
    job.start(tasks)
    assert job.failures.get() == 5
    assert job.results.get() == [('ssh', 'user', 'P@55w0rd!', '127.0.0.1', 22)]


def test_abort_match(ssh_service):
    ssh_host, ssh_port = ssh_service
    tasks = [
        ('ssh', 'user', 'Password', ssh_host, ssh_port),
        ('ssh', 'user', 'Password', ssh_host, ssh_port),
        ('ssh', 'user', 'P@55w0rd!', ssh_host, ssh_port),
        ('ssh', 'user', 'Password', ssh_host, ssh_port),
        ('ssh', 'user', 'Password', ssh_host, ssh_port),
    ]
    job = jobs.Job(abort_match=True)
    job.start(tasks)
    assert job.attempts.get() == 1
    assert job.results.get() == [('ssh', 'user', 'P@55w0rd!', '127.0.0.1', 22)]
