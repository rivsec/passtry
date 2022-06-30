import itertools
import re
import uuid
from urllib import parse
import shlex
import threading
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
DEFAULT_WORKERS_NO = 8
DEFAULT_MAX_FAILED = 10


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

    def __init__(self, workers_no=DEFAULT_WORKERS_NO, max_failed=DEFAULT_MAX_FAILED, abort_match=False, watch_failures=True):
        self.workers_no = workers_no
        self.max_failed = max_failed
        self.abort_match = abort_match
        self.watch_failures = watch_failures
        self.failures = Counter()
        self.attempts = Counter()
        self.results = Results()
        self.queue = queue.Queue()

    def task_to_dict(self, task):
        return {TASK_STRUCT[idx]: tsk for idx, tsk in enumerate(task)}

    def normalize(self, *iterables):
        iters = [[None] if params is None else params for params in iterables]
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
                result = cls.execute(task)
            except exceptions.ConnectionFailed:
                logs.debug(f'Connection failed for {task}')
                if self.watch_failures and failures.get() == self.max_failed:
                    logs.info(f'Too many failed connections, aborting!')
                    self.tasks_clear(queue)
                else:
                    if self.watch_failures:
                        queue.put(task)
                    failures.inc()
                continue
            except Exception as exc:
                logs.debug(f'Task failed with {exc}')
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

    def output(self):
        return [self.prettify(result) for result in self.results.get() if result]

    def start(self, tasks):
        for _ in range(self.workers_no):
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
