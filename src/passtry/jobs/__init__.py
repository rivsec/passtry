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
    2: 'secrets',
    3: 'hosts',
    4: 'ports',
}
TASK_STRUCT_BY_NAME = {val: idx for idx, val in enumerate(TASK_STRUCT.values())}
THREADS_NUMBER = 8
FAILED_NUMBER = 10
CONNECTIONS_TIMEOUT = 10
TIME_WAIT = 0.1
TIME_RANDOMIZE = 0
TIME_STATISTICS = 5


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
            first_match=False,
            watch_failures=True,
            enable_statistics=False,
            time_statistics=TIME_STATISTICS
        ):
        self.threads_number = threads_number
        self.failed_number = failed_number
        self.connections_timeout = connections_timeout
        self.time_wait = time_wait
        self.time_randomize = time_randomize
        self.first_match = first_match
        self.watch_failures = watch_failures
        self.enable_statistics = enable_statistics
        self.time_statistics = time_statistics
        self.failures = Counter()
        self.attempts = Counter()
        self.results = Results()
        self.queue = queue.Queue()

    def task_to_dict(self, task):
        return {TASK_STRUCT[idx]: tsk for idx, tsk in enumerate(task)}

    def combine(self, *iterables):
        """Provides combinations of values in separate lists

        """
        # NOTE: Replace empty set() with [None] for common "interface"
        iters = [params if params else [None] for params in iterables]
        return [list(params) for params in itertools.product(*iters)]

    def replace(self, primary, secondary):
        """Overwrites elements in the second list with the contents
        of the first one and checks for duplicates before adding.

        """
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
        """Returns URI string containing all information required for connection.

        """
        return '{services}://{usernames}:{secrets}@{hosts}:{ports}'.format(**self.task_to_dict(task))

    def cleanup(self, param):
        """Splits command line argument separated with `+`.

        """
        if param is None or param == '':
            return
        return shlex.split(' '.join(SPLIT_REGEX.split(param)[1::2]))

    def split(self, uri):
        """Dissects URI string into components (services[], usernames[], secrets[], targets[], ports[]).

        """
        parsed = parse.urlparse(uri)
        uri_services = self.cleanup(parsed.scheme)
        invalid = [srv for srv in uri_services if srv not in services.Service.registry]
        if any(invalid):
            raise exceptions.ConfigurationError('Invalid service')
        uri_usernames = self.cleanup(parsed.username)
        uri_secrets = self.cleanup(parsed.password)
        uri_targets = self.cleanup(parsed.hostname)
        if parsed.port and len(uri_services) > 1:
            raise exceptions.ConfigurationError('Port numbers cannot be specified when multiple services are tested within a single URI')
        else:
            uri_ports = [parsed.port] if parsed.port else None
        return [uri_services, uri_usernames, uri_secrets, uri_targets, uri_ports]

    def tasks_clear(self, queue):
        """Removes all items from the Queue to stop workers gracefully.

        """
        with queue.mutex:
            queue.queue.clear()
            queue.unfinished_tasks = 0
            queue.all_tasks_done.notify_all()

    def stats(self):
        while True:
            time.sleep(self.time_statistics)
            logs.info(f'Attempts: {self.attempts.get()} | Failed connections: {self.failures.get()} | Matched credentials: {len(self.results.get())}')

    def worker(self):
        """A generic thread worker function.

        """
        while True:
            task = self.queue.get()
            if task is None:
                break
            try:
                cls = services.Service.registry[task[0]]
            except KeyError:
                raise exceptions.ConfigurationError(f'Unknown service `{task[0]}`')
            try:
                result = cls.execute(task, self.connections_timeout)
            except exceptions.ConnectionFailed:
                logs.debug(f'Connection failed for {task}')
                self.failures.inc()
                if self.watch_failures:
                    if self.failures.get() == self.failed_number:
                        logs.info(f'Too many failed connections, aborting!')
                        self.tasks_clear(self.queue)
                        continue
                    else:
                        logs.debug(f'Putting {task} back to the queue')
                self.queue.put(task)
            else:
                self.attempts.inc()
                if result:
                    logs.debug(f'Connection successful for {task}')
                    self.results.add(task)
                    # NOTE: Finish work if abort on first match is enabled.
                    if self.first_match:
                        logs.info(f'Found a first match, done!')
                        self.tasks_clear(self.queue)
            wait_time = self.time_wait
            if self.time_randomize:
                wait_time += round(random.uniform(0, self.time_randomize), 1)
            time.sleep(wait_time)
            # NOTE: This "magic" is due to queue possibly being emptied in another thread.
            if self.queue.unfinished_tasks:
                self.queue.task_done()

    def output(self):
        """Returns list of URIs with confirmed credentials.

        """
        return [self.prettify(result) for result in self.results.get() if result]

    def start(self, tasks):
        """Main entry point.

        """
        for _ in range(self.threads_number):
            threading.Thread(target=self.worker, daemon=True).start()
        if self.enable_statistics:
            threading.Thread(target=self.stats, daemon=True).start()
        for task in tasks:
            self.queue.put(task)
        self.queue.join()
