import pytest

from passtry import (
    logs,
    jobs,
)


def test_combining_lists():
    targets = ('example.com', 'ssh.example.com')
    usernames = ('root', 'guest')
    passwords = ('Password', 'Passw0rd')
    ports = (22, 8222)
    services = ('ssh',)
    assert set(jobs.Job().normalize(services, usernames, passwords, targets, ports)) == {
        ('ssh', 'guest', 'Passw0rd', 'example.com', 22),
        ('ssh', 'guest', 'Passw0rd', 'example.com', 8222),
        ('ssh', 'guest', 'Passw0rd', 'ssh.example.com', 22),
        ('ssh', 'guest', 'Passw0rd', 'ssh.example.com', 8222),
        ('ssh', 'guest', 'Password', 'example.com', 22),
        ('ssh', 'guest', 'Password', 'example.com', 8222),
        ('ssh', 'guest', 'Password', 'ssh.example.com', 22),
        ('ssh', 'guest', 'Password', 'ssh.example.com', 8222),
        ('ssh', 'root', 'Passw0rd', 'example.com', 22),
        ('ssh', 'root', 'Passw0rd', 'example.com', 8222),
        ('ssh', 'root', 'Passw0rd', 'ssh.example.com', 22),
        ('ssh', 'root', 'Passw0rd', 'ssh.example.com', 8222),
        ('ssh', 'root', 'Password', 'example.com', 22),
        ('ssh', 'root', 'Password', 'example.com', 8222),
        ('ssh', 'root', 'Password', 'ssh.example.com', 22),
        ('ssh', 'root', 'Password', 'ssh.example.com', 8222),
    }


def test_combining_lists_empty():
    targets = ('example.com', 'ssh.example.com')
    usernames = ('root', 'guest')
    passwords = [None]
    ports = (22, 8222)
    services = ('ssh',)
    assert set(jobs.Job().normalize(services, usernames, passwords, targets, ports)) == {
        ('ssh', 'root', None, 'example.com', 22),
        ('ssh', 'root', None, 'example.com', 8222),
        ('ssh', 'root', None, 'ssh.example.com', 22),
        ('ssh', 'root', None, 'ssh.example.com', 8222),
        ('ssh', 'guest', None, 'example.com', 22),
        ('ssh', 'guest', None, 'example.com', 8222),
        ('ssh', 'guest', None, 'ssh.example.com', 22),
        ('ssh', 'guest', None, 'ssh.example.com', 8222)
    }


def test_uri_split_exclusive_services_ports():
    """Port numbers cannot be declared if more than one service is tested"""
    with pytest.raises(Exception):
        jobs.Job().split('ssh+ftp://admin:password@example.com:22')


def test_uri_split_malformed():

    job = jobs.Job()

    with pytest.raises(Exception):
        job.split('example.com')

    with pytest.raises(Exception):
        job.split('http://')


def test_uri_split_service_exists():
    with pytest.raises(Exception):
        jobs.Job().split('hXXp://example.com')


def test_uri_split_set_port():
    job = jobs.Job()

    assert jobs.Job().split('ssh://admin:password@example.com:22') == [
        ('ssh', 'admin', 'password', 'example.com', 22),
    ]

    assert jobs.Job().split('ssh://admin:password@example.com:2222') == [
        ('ssh', 'admin', 'password', 'example.com', 2222),
    ]


def test_uri_split_no_default_port():
    job = jobs.Job()

    assert job.split('http://example.com') == [
        ('http', None, None, 'example.com', None),
    ]


def test_uri_split_override_port():
    job = jobs.Job()

    assert job.split('http://example.com:81') == [
        ('http', None, None, 'example.com', 81),
    ]


def test_uri_split_multiple_services():
    job = jobs.Job()

    assert set(job.split('ssh+ftp://admin:password@example.com')) == {
        ('ftp', 'admin', 'password', 'example.com', None),
        ('ssh', 'admin', 'password', 'example.com', None),
    }


def test_uri_split_plus_in_passwords():
    job = jobs.Job()

    result = job.split('ssh://admin:password+\'pass+word2\'+"password+3"@example.com')
    assert set(job.split('ssh://admin:password+\'pass+word2\'+"password+3"@example.com')) == {
        ('ssh', 'admin', 'password', 'example.com', None),
        ('ssh', 'admin', 'pass+word2', 'example.com', None),
        ('ssh', 'admin', 'password+3', 'example.com', None),
    }


def test_uri_split_no_username():
    job = jobs.Job()

    assert set(job.split('ssh+ftp://:password@example.com')) == {
        ('ftp', None, 'password', 'example.com', None),
        ('ssh', None, 'password', 'example.com', None),
    }


def test_uri_split_no_password():
    job = jobs.Job()

    assert set(job.split('ssh+ftp://admin@example.com')) == {
        ('ftp', 'admin', None, 'example.com', None),
        ('ssh', 'admin', None, 'example.com', None),
    }


def test_uri_split_multiple_targets():
    job = jobs.Job()

    assert set(job.split('ssh+ftp://admin+root+user:password+Passw0rd@example.com+other.example.com')) == {
        ('ssh', 'admin', 'password', 'example.com', None),
        ('ssh', 'root', 'password', 'example.com', None),
        ('ssh', 'user', 'password', 'example.com', None),
        ('ssh', 'admin', 'Passw0rd', 'example.com', None),
        ('ssh', 'root', 'Passw0rd', 'example.com', None),
        ('ssh', 'user', 'Passw0rd', 'example.com', None),
        ('ssh', 'admin', 'password', 'other.example.com', None),
        ('ssh', 'root', 'password', 'other.example.com', None),
        ('ssh', 'user', 'password', 'other.example.com', None),
        ('ssh', 'admin', 'Passw0rd', 'other.example.com', None),
        ('ssh', 'root', 'Passw0rd', 'other.example.com', None),
        ('ssh', 'user', 'Passw0rd', 'other.example.com', None),
        ('ftp', 'admin', 'password', 'example.com', None),
        ('ftp', 'root', 'password', 'example.com', None),
        ('ftp', 'user', 'password', 'example.com', None),
        ('ftp', 'admin', 'Passw0rd', 'example.com', None),
        ('ftp', 'root', 'Passw0rd', 'example.com', None),
        ('ftp', 'user', 'Passw0rd', 'example.com', None),
        ('ftp', 'admin', 'password', 'other.example.com', None),
        ('ftp', 'root', 'password', 'other.example.com', None),
        ('ftp', 'user', 'password', 'other.example.com', None),
        ('ftp', 'admin', 'Passw0rd', 'other.example.com', None),
        ('ftp', 'root', 'Passw0rd', 'other.example.com', None),
        ('ftp', 'user', 'Passw0rd', 'other.example.com', None),
    }
