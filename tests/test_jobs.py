import pytest

from passtry import (
    exceptions,
    jobs,
)


def test_max_failed_no_results(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(threads_number=1, failed_number=3)
    job.start(
        [f'ssh:9991,9992,9993,{ssh_port},9994,9995'], [ssh_host], ['user'], ['P@55w0rd!']
    )
    assert job.failed.get() == 3
    assert job.successful.get() == 0
    assert job.results.get() == list()


def test_max_failed_increased_results(ssh_service):
    ssh_host, ssh_port = ssh_service
    # NOTE: Must disable retry so the task put back to the queue will not increase the failures
    #       value and enable first match to stop.
    job = jobs.Job(threads_number=1, failed_number=4, retry_failed=False, first_match=True)
    job.start(
        [f'ssh:9991,9992,9993,{ssh_port},9994,9995'], [ssh_host], ['user'], ['P@55w0rd!']
    )
    assert job.failed.get() == 3
    assert job.successful.get() == 1
    assert job.results.get() == [('ssh', str(ssh_port), ssh_host, 'user', 'P@55w0rd!', None)]


def test_max_failed_disable_failures_first_match_no_retry(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(threads_number=1, failed_number=3, retry_failed=False, watch_failures=False, first_match=True)
    job.start(
        [f'ssh:9991,9992,9993,9994,9995,{ssh_port}'], [ssh_host], ['user'], ['P@55w0rd!', 'Password']
    )
    assert job.attempts.get() == 6
    assert job.failed.get() == 5
    assert job.successful.get() == 1
    assert job.results.get() == [('ssh', str(ssh_port), ssh_host, 'user', 'P@55w0rd!', None)]


def test_first_match(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(threads_number=1, first_match=True)
    job.start(
        ['ssh'], [ssh_host], ['user', 'user2'], ['Password!', 'P@55w0rd!', 'Password']
    )
    assert job.attempts.get() == 2
    assert job.successful.get() == 2
    assert job.results.get() == [('ssh', str(ssh_port), ssh_host, 'user', 'P@55w0rd!', None)]


def test_override_service_port(ssh_service):
    ssh_host, ssh_port = ssh_service
    job = jobs.Job(threads_number=1, first_match=True)
    job.start(
        ['ssh:2221,2222'], [f'{ssh_host}:22'], ['user', 'user2'], ['Password!', 'P@55w0rd!', 'Password']
    )
    assert job.attempts.get() == 2
    assert job.successful.get() == 2
    assert job.results.get() == [('ssh', str(ssh_port), ssh_host, 'user', 'P@55w0rd!', None)]
