from urllib import parse

import requests

from passtry import (
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
        mapping['path'] = options.get('path', '')
        mapping['query'] = options.get('query', '')
        mapping['fragment'] = options.get('fragment', '')
        return mapping


class HttpBasicAuth(HttpMixin, services.Service):

    port = 80
    service = 'http-basic'
    scheme = 'http'

    @classmethod
    def execute(cls, task, timeout):
        logs.debug(f'{cls.__name__} is executing {task}')
        kwargs = cls.map_kwargs(task)
        url = parse.urlunsplit((cls.scheme, kwargs['netloc'], kwargs['path'], kwargs['query'], kwargs['fragment']))
        response = requests.get(url, auth=requests.auth.HTTPBasicAuth(kwargs['user'], kwargs['pass']), verify=False)
        if response.status_code == 200:
            return True
        else:
            return False


class HttpsBasicAuth(HttpBasicAuth):

    port = 443
    service = 'https-basic'
    scheme = 'https'
