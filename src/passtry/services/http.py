from urllib import parse

import requests

from passtry import (
    exceptions,
    logs,
    services,
)


class HttpMixin:

    @classmethod
    def map_kwargs(cls, task):
        mapping = {
            'netloc': task[3],
            'user': task[1],
            'pass': task[2],
            'port': int(task[4]),
        }
        options = task[5]
        mapping['path'] = options.get('path', '') if options else ''
        mapping['query'] = options.get('query', '') if options else ''
        mapping['fragment'] = options.get('fragment', '') if options else ''
        return mapping


class HttpBasicAuth(HttpMixin, services.Service):

    port = 80
    service = 'http-basic'
    scheme = 'http'

    @classmethod
    def execute(cls, task, timeout):
        logs.logger.debug(f'{cls.__name__} is executing {task}')
        kwargs = cls.map_kwargs(task)
        url = parse.urlunsplit((cls.scheme, kwargs['netloc'], kwargs['path'], kwargs['query'], kwargs['fragment']))
        try:
            response = requests.get(url, auth=requests.auth.HTTPBasicAuth(kwargs['user'], kwargs['pass']), verify=False, timeout=timeout)
        except requests.exceptions.Timeout:
            logs.logger.debug(f'{cls.__name__} connection failed (timed out?) for {task}')
            raise exceptions.ConnectionFailed
        if response.status_code == 200:
            return True
        else:
            return False


class HttpsBasicAuth(HttpBasicAuth):

    port = 443
    service = 'https-basic'
    scheme = 'https'
