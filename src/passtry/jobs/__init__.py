from urllib import parse
import itertools
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
THREADS_NUMBER = 20
FAILED_NUMBER = 3
CONNECTIONS_TIMEOUT = 2
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

    def set(self, items):
        with self._lock:
            self._items = items

    def get(self):
        with self._lock:
            return self._items


class Ignored:

    def __init__(self):
        self._items = dict()
        self._lock = threading.Lock()

    def inc(self, item):
        with self._lock:
            if item not in self._items:
                self._items[item] = 0
            self._items[item] += 1

    def get(self, item):
        with self._lock:
            if item not in self._items:
                self._items[item] = 0
            return self._items[item]


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
            time_statistics=TIME_STATISTICS,
            randomize=True,
            output_file=None
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
        self.randomize = randomize
        self.output_file = output_file
        self.attempts = Counter()
        self.successful = Counter()
        self.failed = Counter()
        self.results = Results()
        self.ignored = Ignored()
        self.tasks = list()
        self.total = None
        self.running = False
        self._output = None
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
                    cred = line.strip().split(delimiter)
                    if len(cred) < 2:
                        raise exceptions.DataError(f'Invalid combo file! Line: {line}')
                    else:
                        result.append(tuple(cred))
            except ValueError:
                raise exceptions.DataError('Error occured while processing combo file')
        return result

    def prettify(self, task):
        """Returns URI string containing all information required for connection.

        """
        task_dict = self.task_to_dict(task)
        prettify_method = services_module.Service.registry[task_dict['services']].prettify
        return prettify_method(task_dict)

    def worker_stats(self):
        while self.running:
            percentage = int(abs(len(self.tasks) / self.total * 100 - 100))
            logs.logger.info(
                f'Attempts: {self.attempts.get()} | '
                f'Successful: {self.successful.get()} | '
                f'Failed: {self.failed.get()} | '
                f'Credentials: {len(self.results.get())} | '
                f'Pending: {len(self.tasks)} / {self.total} [{percentage}%]'
            )
            time.sleep(self.time_statistics)

    def worker_tasks(self):
        thread = threading.current_thread()
        while self.running:
            try:
                if self.randomize:
                    task = self.tasks.pop(random.randrange(len(self.tasks)))
                else:
                    task = self.tasks.pop()
            except (ValueError, IndexError):
                self.running = False
                break
            unique_key = (task[0], task[1], task[2])
            if self.watch_failures:
                if self.ignored.get(unique_key) >= self.failed_number:
                    # FIXME: Needs a better approach (erasing other occurrences). Current
                    #        solution has a race condition, hence the `>=`.
                    logs.logger.debug(f'/ {thread.name} / Ignoring: {task}')
                    continue
            try:
                cls = services_module.Service.registry[task[0]]
            except KeyError:
                raise exceptions.ConfigurationError(f'Unknown service `{task[0]}`')
            self.attempts.inc()
            logs.logger.debug(f'/ {thread.name} / Executing: {task}')
            try:
                result = cls.execute(task, self.connections_timeout)
            except exceptions.ConnectionFailed:
                logs.logger.debug(f'/ {thread.name} / Connection failed: {task}')
                self.failed.inc()
                if self.watch_failures:
                    # NOTE: Increase counter for failed connection for given service:port:host combination.
                    logs.logger.debug(f'/ {thread.name} / Increasing ignored count: {unique_key}')
                    self.ignored.inc(unique_key)
                if self.retry_failed:
                    logs.logger.debug(f'/ {thread.name} / Putting back: {task}')
                    self.tasks.append(task)
            else:
                self.successful.inc()
                logs.logger.debug(f'/ {thread.name} / Connection successful: {task}')
                if result:
                    logs.logger.debug(f'/ {thread.name} / [VALIDATED] credentials: {task}')
                    print(self.prettify(task))
                    self.results.add(task)
                    # NOTE: Finish work if abort on first match is enabled.
                    if self.first_match:
                        # FIXME: Same issues as with ignored: a matching password can end up
                        #        in two different threads if small number of tasks. Edge case
                        #        but still a case.
                        self.tasks.clear()
                        self.running = False
                        break
            wait_time = self.time_wait
            if self.time_randomize:
                wait_time += round(random.uniform(0, self.time_randomize), 1)
            time.sleep(wait_time)

    @property
    def output(self):
        """Returns list of URIs with confirmed credentials.

        """
        if self._output is None:
            self._output = [self.prettify(result) for result in self.results.get() if result]
        return self._output

    def put(self, service, ports, target, username, secret, service_options):
        try:
            host, port = target.split(':')
        except ValueError:
            host, port = target, None
        if port:
            self.tasks.append((service, int(port), host, username, secret, service_options))
        else:
            for port in ports.split(','):
                try:
                    port = int(port)
                except ValueError:
                    pass
                else:
                    self.tasks.append((service, port, host, username, secret, service_options))

    def start(self, services, targets, usernames=None, secrets=None, options=None, combos=None):
        """Main entry point.

        """
        if options is None:
            options = dict()
        if combos is None:
            combos = list()

        services = list(services)

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

        logs.logger.info('Adding tasks...')
        creds = list(itertools.product(usernames, secrets))
        creds.extend(combos)
        for prod in itertools.product(services, targets, creds):
            service, ports = prod[0]
            service_options = options.get(service, None)
            username, secret = prod[2]
            self.put(service, ports, prod[1], username, secret, service_options)

        self.total = len(self.tasks)
        logs.logger.info(f'Added {self.total} tasks')
        threads = [
            threading.Thread(
                name='Worker-' + str(idx),
                target=self.worker_tasks,
                daemon=True
            ) for idx in range(self.threads_number)
        ]

        self.running = True

        logs.logger.info('Running')
        for thread in threads:
            thread.start()

        if self.enable_statistics:
            stats = threading.Thread(target=self.worker_stats, daemon=True)
            stats.start()
            threads.append(stats)

        for thread in threads:
            thread.join()

        if self.first_match:
            if len(self.results.get()):
                self.results.set([self.results.get()[0]])

        failed = self.failed.get()
        if failed:
            logs.logger.info(f'Connection failed {failed} times')
        if self.output:
            if self.output_file:
                # NOTE: Write order doesn't matter.
                with open(self.output_file, 'a+') as fil:
                    fil.writelines(self.output)
