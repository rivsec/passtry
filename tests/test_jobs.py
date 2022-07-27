import pytest

from passtry import (
    exceptions,
    jobs,
)


def test_max_failed_no_results(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(threads_number=1, failed_number=2)
    job.start(
        [f'ssh:9991,9992,9993,9994,9995'], [ssh_host], ['user'], ['P@55w0rd!']
    )
    assert job.failed.get() == 10
    assert job.successful.get() == 0
    assert job.results.get() == list()


def test_max_failed_results_retry(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(threads_number=1, failed_number=2, retry_failed=True, first_match=True, randomize=False)
    job.start(
        [f'ssh:9991,9992,9993,{ssh_port},9994,9995'], [ssh_host], ['user'], ['P@55w0rd!']
    )
    assert job.failed.get() == 4
    assert job.attempts.get() == 5
    assert job.successful.get() == 1
    assert job.results.get() == [('ssh', ssh_port, ssh_host, 'user', 'P@55w0rd!', None)]


def test_max_failed_results_retry_continue(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(threads_number=1, failed_number=3, retry_failed=True, first_match=False, randomize=False)
    job.start(
        [f'ssh:9991,9992,9993,{ssh_port},9994,9995'], [ssh_host], ['user'], ['P@55w0rd!']
    )
    assert job.failed.get() == 15
    assert job.attempts.get() == 16
    assert job.successful.get() == 1
    assert job.results.get() == [('ssh', ssh_port, ssh_host, 'user', 'P@55w0rd!', None)]


def test_max_failed_results_no_retry(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(threads_number=1, failed_number=2, retry_failed=False, first_match=True, randomize=False)
    job.start(
        [f'ssh:9991,9992,9993,{ssh_port},9994,9995'], [ssh_host], ['user'], ['P@55w0rd!']
    )
    assert job.failed.get() == 2
    assert job.attempts.get() == 3
    assert job.successful.get() == 1
    assert job.results.get() == [('ssh', ssh_port, ssh_host, 'user', 'P@55w0rd!', None)]


def test_max_failed_disable_failures_first_match_no_retry(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(threads_number=1, failed_number=1, retry_failed=False, watch_failures=False, first_match=True, randomize=False)
    job.start(
        [f'ssh:9991,9992,9993,9994,9995,{ssh_port}'], [ssh_host], ['user'], ['P@55w0rd!', 'Password']
    )
    assert job.attempts.get() == 7
    assert job.failed.get() == 5
    assert job.successful.get() == 2
    assert len(job.results.get()) == 1


def test_first_match(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(first_match=True, randomize=False)
    job.start(
        ['ssh'], [ssh_host], ['user2', 'user'], ['Password!', 'P@55w0rd!', 'Password']
    )
    assert job.attempts.get() == 6
    assert job.successful.get() == 6
    assert len(job.results.get()) == 1


def test_override_service_port(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(first_match=True, randomize=False)
    job.start(
        ['ssh:2221,2222'], [f'{ssh_host}:22'], ['user2', 'user'], ['Password!', 'P@55w0rd!', 'Password']
    )
    assert job.attempts.get() == 6
    assert job.successful.get() == 6
    assert len(job.results.get()) == 1


def test_fail_per_host_port(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(retry_failed=False, failed_number=1)
    job.start(
        ['ssh:22,2221,2222,2223,2224'], [ssh_host], ['user'], ['Password!', 'P@55w0rd!', 'Password']
    )
    # NOTE: This is "doing the best" approach to minimize number of repetitions
    #       for failed hosts, hence the specific number can't be predicted.
    #       Needs better solution, see line `if self.ignored.get(host_port) >= self.failed_number`
    assert job.ignored.get(('ssh', 2221, ssh_host)) >= 1
    assert job.ignored.get(('ssh', 2222, ssh_host)) >= 1
    assert job.ignored.get(('ssh', 2223, ssh_host)) >= 1
    assert job.ignored.get(('ssh', 2224, ssh_host)) >= 1
    assert job.results.get() == [('ssh', ssh_port, ssh_host, 'user', 'P@55w0rd!', None)]
