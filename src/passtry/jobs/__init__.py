import concurrent.futures
import itertools
import uuid

from passtry import (
    logs,
    protocols,
)


class Job:

    def __init__(self):
        self.results = list()
        self.tasks = list()

    def task_to_dict(self, task):
        return {
            'protocol': task[0],
            'username': task[1],
            'password': task[2],
            'host': task[3],
            'port': task[4],
        }

    def normalize(self, *iterables):
        return [params for params in itertools.product(*iterables)]

    def prettify(self, task):
        return '{protocol}://{username}:{password}@{host}:{port}'.format(**self.task_to_dict(task))

    def start(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = dict()
            for task in self.tasks:
                fid = uuid.uuid4()
                try:
                    cls = protocols.Protocol.registry[task[0]]
                except KeyError:
                    raise Exception(f'Unknown protocol `{task[0]}`')  # TODO: Custom configuration/arguments exception
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
