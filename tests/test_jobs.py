from passtry import (
    logs,
    jobs,
)


def test_jobs_combining_lists():
    hosts = ('example.com', 'ssh.example.com')
    usernames = ('root', 'guest')
    passwords = ('Password', 'Passw0rd')
    ports = (22, 8222)
    protocols = ('ssh',)
    assert set(jobs.Job().normalize(protocols, usernames, passwords, hosts, ports)) == {
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


def test_jobs_appending_results():
    pass
