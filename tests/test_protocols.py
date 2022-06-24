from passtry import jobs


def test_ssh_connection():
    job = jobs.Job()
    job.tasks = [
        ('ssh', 'user', 'Password', '172.16.191.136', 22),  # TODO: Dockerize SSH servers for tests
        ('ssh', 'user', 'P@55w0rd!', '172.16.191.136', 2222),
    ]
    results = job.start()
    output = [job.prettify(result) for result in results]
    assert output == ['ssh://user:P@55w0rd!@172.16.191.136:2222']
