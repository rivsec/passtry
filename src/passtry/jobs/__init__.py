from urllib import parse
import itertools
import queue
import random
import threading
import time
import urllib3

from passtry import (
    exceptions,
    logs,
)
from passtry import services as services_module


TASK_STRUCT = {
    0: 'services',
    1: 'ports',
    2: 'targets',
    3: 'usernames',
    4: 'secrets',
    5: 'options',
}
THREADS_NUMBER = 10
FAILED_NUMBER = 10
CONNECTIONS_TIMEOUT = 10
TIME_WAIT = 0.1
TIME_RANDOMIZE = 0
TIME_STATISTICS = 5


class Counter:

    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def inc(self):
        with self._lock:
            self._value += 1

    def get(self):
        with self._lock:
            return self._value


class Results:

    def __init__(self):
        self._items = list()
        self._lock = threading.Lock()

    def add(self, item):
        with self._lock:
            self._items.append(item)

    def get(self):
        with self._lock:
            return self._items


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
            retry_failed=True,
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
        self.retry_failed = retry_failed
        self.enable_statistics = enable_statistics
        self.time_statistics = time_statistics
        self.attempts = Counter()
        self.successful = Counter()
        self.failed = Counter()
        self.results = Results()
        self.queue = queue.Queue()
        # NOTE: Disable `Unverified HTTPS request is being made` warning.
        # FIXME: Any better place to put this to guarantee execution?
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def task_to_dict(self, task):
        try:
            return {TASK_STRUCT[idx]: tsk for idx, tsk in enumerate(task)}
        except KeyError:
            raise exceptions.DataError(f'Task {task} contains invalid number of elements')

    def read_file(self, file_obj):
        if file_obj is None:
            result = list([None])
        else:
            result = list()
            for line in file_obj:
                result.append(line.rstrip('\n'))
        return result

    def read_combo(self, file_obj, delimiter=None):
        result = list()
        if file_obj is not None:
            try:
                for line in file_obj:
                    result.append(tuple(line.strip().split(delimiter)))
            except ValueError:
                raise exceptions.DataError('Error occured while processing combo file')
        return result

    def prettify(self, task):
        """Returns URI string containing all information required for connection.

        """
        task_dict = self.task_to_dict(task)
        prettify_method = services_module.Service.registry[task_dict['services']].prettify
        return prettify_method(task_dict)

    def tasks_clear(self, queue):
        """Removes all items from the Queue to stop workers gracefully.

        """
        with queue.mutex:
            queue.queue.clear()
            queue.unfinished_tasks = 0
            queue.all_tasks_done.notify_all()

    def worker_stats(self):
        while True:
            time.sleep(self.time_statistics)
            logs.logger.info(
                f'Attempts: {self.attempts.get()} | '
                f'Successful connections: {self.successful.get()} | '
                f'Failed connections: {self.failed.get()} | '
                f'Matched credentials: {len(self.results.get())}'
            )

    def worker_tasks(self):
        """A generic thread worker function.

        """
        while True:
            task = self.queue.get()
            if task is None:
                break
            try:
                cls = services_module.Service.registry[task[0]]
            except KeyError:
                raise exceptions.ConfigurationError(f'Unknown service `{task[0]}`')
            self.attempts.inc()
            try:
                result = cls.execute(task, self.connections_timeout)
            except exceptions.ConnectionFailed:
                logs.logger.debug(f'Connection failed for {task}')
                self.failed.inc()
                if self.watch_failures:
                    if self.failed.get() == self.failed_number:
                        logs.logger.info(f'Too many failed connections, aborting!')
                        self.tasks_clear(self.queue)
                        continue
                if self.retry_failed:
                    logs.logger.debug(f'Putting {task} back to the queue')
                    self.queue.put(task)
            else:
                self.successful.inc()
                logs.logger.debug(f'Connection successful for {task}')
                if result:
                    logs.logger.debug(f'Validated following credentials: {task}')
                    print(self.prettify(task))
                    self.results.add(task)
                    # NOTE: Finish work if abort on first match is enabled.
                    if self.first_match:
                        logs.logger.info(f'Found a first match, done!')
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
        logs.logger.debug('output()')
        return [self.prettify(result) for result in self.results.get() if result]

    def start(self, services, targets, usernames=None, secrets=None, options=None, combos=None):
        """Main entry point.

        """
        if options is None:
            options = dict()

        services = list(services)

        logs.logger.debug('Starting thread workers')
        for _ in range(self.threads_number):
            threading.Thread(target=self.worker_tasks, daemon=True).start()

        logs.logger.debug('Filling ports')
        # NOTE: Parse `services` and build a list of tuples with ports taken from respective classes.
        for idx, service in enumerate(services):
            srv = service.split(':')
            if len(srv) == 1:
                try:
                    srv.append(str(services_module.Service.registry[srv[0]].port))
                except KeyError:
                    raise exceptions.ConfigurationError(f'Unknown service `{srv[0]}`!')
            services[idx] = srv

        logs.logger.info(f'Running!')
        if combos:
            for prod in itertools.product(services, targets, combos):
                service, ports = prod[0]
                service_options = options.get(service, None)
                try:
                    username, secret = prod[2]
                except ValueError:
                    raise exceptions.DataError('Invalid combo file!')
                for port in ports.split(','):
                    self.queue.put((service, port, prod[1], username, secret, service_options))
        if usernames and secrets:
            for prod in itertools.product(services, targets, usernames, secrets):
                service, ports = prod[0]
                service_options = options.get(service, None)
                for port in ports.split(','):
                    self.queue.put((service, port, prod[1], prod[2], prod[3], service_options))
        if self.enable_statistics:
            threading.Thread(target=self.worker_stats, daemon=True).start()
        self.queue.join()
