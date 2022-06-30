from passtry import (
    logs,
    services,
)


class HTTP(services.Service):

    port = 80
    service = 'http'

    @classmethod
    def map_kwargs(cls, task):
        return {
            'hostname': task[3],
            'username': task[1],
            'password': task[2],
            'port': int(task[4]),
        }

    @classmethod
    def execute(cls, task, timeout):
        logs.debug(f'{cls.__name__} is executing {task}')
        kwargs = cls.map_kwargs(task)
        return True
