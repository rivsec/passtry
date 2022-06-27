import concurrent.futures
import itertools
import re
import uuid
from urllib import parse
import shlex

from passtry import (
    logs,
    services,
)


SPLIT_REGEX = re.compile(r"""((?:[^+"']|"[^"]*"|'[^']*')+)""")


class Job:

    def __init__(self):
        self.results = list()
        self.tasks = list()

    def task_to_dict(self, task):
        return {
            'service': task[0],
            'username': task[1],
            'password': task[2],
            'host': task[3],
            'port': task[4],
        }

    def normalize(self, *iterables):
        return [params for params in itertools.product(*iterables)]

    def prettify(self, task):
        return '{service}://{username}:{password}@{host}:{port}'.format(**self.task_to_dict(task))

    def split_part(self, part):
        sliced = ' '.join(SPLIT_REGEX.split(part)[1::2])
        return shlex.split(sliced)

    def split(self, uri):
        parsed = parse.urlparse(uri)
        uri_services = self.split_part(parsed.scheme)
        invalid = [srv for srv in uri_services if srv not in services.Service.registry]
        if any(invalid):
            raise Exception('Invalid service')  # TODO: Custom exception
        uri_usernames = self.split_part(parsed.username) if parsed.username else [None]
        uri_passwords = self.split_part(parsed.password) if parsed.password else [None]
        uri_targets = self.split_part(parsed.hostname)
        if parsed.port:
            if len(uri_services) > 1:
                raise Exception('Port numbers cannot be specified when multiple services are tested within a single URI')  # TODO: Custom exception
            else:
                uri_ports = (parsed.port,)
        else:
            uri_ports = [None]
        return self.normalize(uri_services, uri_usernames, uri_passwords, uri_targets, uri_ports)

    def start(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = dict()
            for task in self.tasks:
                fid = uuid.uuid4()
                try:
                    cls = services.Service.registry[task[0]]
                except KeyError:
                    raise Exception(f'Unknown service `{task[0]}`')  # TODO: Custom configuration/arguments exception
                futures = {executor.submit(cls.execute, fid, task): fid}
            for future in concurrent.futures.as_completed(futures):
                fid = futures[future]
                try:
                    results = future.result()
                    self.results.append(results)
                    logs.debug(f'Task {fid} added {results} to results')
                except Exception as exc:
                    logs.error(f'Task {fid} failed with {exc}')
                    raise exc
                else:
                    logs.debug(f'Task {fid} completed')
        return self.results
