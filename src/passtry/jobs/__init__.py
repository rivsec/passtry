import itertools
import re
import uuid
from urllib import parse
import shlex
import threading
import queue

from passtry import (
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


class Job:

    workers_no = 8

    def __init__(self):
        self.results = list()
        self.tasks = list()
        self.workers = list()
        self.queue = queue.Queue()

    def task_to_dict(self, task):
        return {TASK_STRUCT[idx]: tsk for idx, tsk in enumerate(task)}

    def normalize(self, *iterables):
        iters = [[None] if params is None else params for params in iterables]
        return [list(params) for params in itertools.product(*iters)]

    def merge(self, primary, secondary):
        mapping = primary[0]
        for ele in secondary:
            for idx, _ in enumerate(ele):
                if mapping[idx]:
                    ele[idx] = mapping[idx]

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
            raise Exception('Invalid service')  # TODO: Custom exception
        uri_usernames = self.cleanup(parsed.username)
        uri_passwords = self.cleanup(parsed.password)
        uri_targets = self.cleanup(parsed.hostname)
        if parsed.port and len(uri_services) > 1:
            raise Exception('Port numbers cannot be specified when multiple services are tested within a single URI')  # TODO: Custom exception
        else:
            uri_ports = [parsed.port] if parsed.port else None
        return [uri_services, uri_usernames, uri_passwords, uri_targets, uri_ports]

    def consume(self, tasks):
        self.tasks = tasks

    def worker(self):
        while True:
            task = self.queue.get()
            if task is None:
                break
            try:
                cls = services.Service.registry[task[0]]
            except KeyError:
                raise Exception(f'Unknown service `{task[0]}`')  # TODO: Custom configuration/arguments exception
            try:
                result = cls.execute(task)
            except Exception as exc:
                logs.debug(f'Task failed with {exc}')
            else:
                if result:
                    self.results.append(task)
            self.queue.task_done()

    def start(self):
        for idx in range(self.workers_no):
            thread = threading.Thread(name=str(idx), target=self.worker, daemon=True)
            thread.start()
            self.workers.append(thread)
        for task in self.tasks:
            self.queue.put(task)
        self.queue.join()
