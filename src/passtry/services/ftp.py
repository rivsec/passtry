from passtry import (
    logs,
    services,
)


class FTP(services.Service):

    port = 21
    service = 'ftp'

    @classmethod
    def map_kwargs(cls, task):
        return {
            'hostname': task[3],
            'username': task[1],
            'password': task[2],
            'port': task[4],
        }

    @classmethod
    def execute(cls, fid, task):
        logs.debug(f'{cls.__name__} is executing {fid}')
        kwargs = cls.map_kwargs(task)
        return task