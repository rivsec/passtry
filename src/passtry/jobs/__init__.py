import itertools
import re
import uuid
from urllib import parse
import shlex
import random
import threading
import time
import queue

from passtry import (
    exceptions,
    logs,
    services,
)


SPLIT_REGEX = re.compile(r"""((?:[^+"']|"[^"]*"|'[^']*')+)""")
TASK_STRUCT = {
    0: 'services',
    1: 'usernames',
    2: 'passwords',
    3: 'hosts',
    4: 'ports',
}
TASK_STRUCT_BY_NAME = {val: idx for idx, val in enumerate(TASK_STRUCT.values())}
THREADS_NUMBER = 8
FAILED_NUMBER = 10
CONNECTIONS_TIMEOUT = 10
TIME_WAIT = 0.1
TIME_RANDOMIZE = 0


class Counter:

    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def inc(self):
        with self.lock:
            self.value += 1

    def get(self):
        with self.lock:
            return self.value


class Results:

    def __init__(self):
        self.items = list()
        self.lock = threading.Lock()

    def add(self, item):
        with self.lock:
            self.items.append(item)

    def get(self):
        with self.lock:
            return self.items


class Job:

    def __init__(
            self,
            threads_number=THREADS_NUMBER,
            failed_number=FAILED_NUMBER,
            connections_timeout=CONNECTIONS_TIMEOUT,
            time_wait=TIME_WAIT,
            time_randomize=TIME_RANDOMIZE,
            abort_match=False,
            watch_failures=True
        ):
        self.threads_number = threads_number
        self.failed_number = failed_number
        self.connections_timeout = connections_timeout
        self.time_wait = time_wait
        self.time_randomize = time_randomize
        self.abort_match = abort_match
        self.watch_failures = watch_failures
        self.failures = Counter()
        self.attempts = Counter()
        self.results = Results()
        self.queue = queue.Queue()

    def task_to_dict(self, task):
        return {TASK_STRUCT[idx]: tsk for idx, tsk in enumerate(task)}

    def combine(self, *iterables):
        # NOTE: Replace empty set() with [None] for common "interface"
        iters = [params if params else [None] for params in iterables]
        return [list(params) for params in itertools.product(*iters)]

    def merge(self, primary, secondary):
        mapping = primary[0]
        result = list()
        for ele in secondary:
            for idx, _ in enumerate(ele):
                if mapping[idx]:
                    ele[idx] = mapping[idx]
            if not result.count(ele):
                result.append(ele)
        return result

    def prettify(self, task):
        return '{services}://{usernames}:{passwords}@{hosts}:{ports}'.format(**self.task_to_dict(task))

    def cleanup(self, param):
        if param is None or param == '':
            return
        return shlex.split(' '.join(SPLIT_REGEX.split(param)[1::2]))

    def split(self, uri):
        parsed = parse.urlparse(uri)
        uri_services = self.cleanup(parsed.scheme)
        invalid = [srv for srv in uri_services if srv not in services.Service.registry]
        if any(invalid):
            raise exceptions.ConfigurationError('Invalid service')
        uri_usernames = self.cleanup(parsed.username)
        uri_passwords = self.cleanup(parsed.password)
        uri_targets = self.cleanup(parsed.hostname)
        if parsed.port and len(uri_services) > 1:
            raise exceptions.ConfigurationError('Port numbers cannot be specified when multiple services are tested within a single URI')
        else:
            uri_ports = [parsed.port] if parsed.port else None
        return [uri_services, uri_usernames, uri_passwords, uri_targets, uri_ports]

    def tasks_clear(self, queue):
        with queue.mutex:
            queue.queue.clear()
            queue.unfinished_tasks = 0
            queue.all_tasks_done.notify_all()

    def worker(self, failures, attempts, queue, results):
        while True:
            task = queue.get()
            if task is None:
                self.tasks_clear(queue)
                continue
            try:
                cls = services.Service.registry[task[0]]
            except KeyError:
                raise exceptions.ConfigurationError(f'Unknown service `{task[0]}`')
            try:
                result = cls.execute(task, self.connections_timeout)
            except exceptions.ConnectionFailed:
                logs.debug(f'Connection failed for {task}')
                if self.watch_failures and failures.get() == self.failed_number:
                    logs.info(f'Too many failed connections, aborting!')
                    self.tasks_clear(queue)
                else:
                    if self.watch_failures:
                        queue.put(task)
                    failures.inc()
                continue
            else:
                attempts.inc()
                if result:
                    logs.debug(f'Connection successful for {task}')
                    results.add(task)
                    if self.abort_match:
                        self.tasks_clear(queue)
            finally:
                # NOTE: This "magic" is due to queue possibly being emptied in another thread.
                if queue.unfinished_tasks:
                    queue.task_done()
                wait_time = self.time_wait
                if self.time_randomize:
                    wait_time += round(random.uniform(0, self.time_randomize), 1)
                time.sleep(wait_time)

    def output(self):
        return [self.prettify(result) for result in self.results.get() if result]

    def start(self, tasks):
        for _ in range(self.threads_number):
            threading.Thread(
                target=self.worker,
                args=(
                    self.failures,
                    self.attempts,
                    self.queue,
                    self.results
                ),
                daemon=True
            ).start()
        for task in tasks:
            self.queue.put(task)
        self.queue.join()
