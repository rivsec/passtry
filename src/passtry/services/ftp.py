import ftplib

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
            'host': task[3],
            'user': task[1],
            'passwd': task[2],
            'port': int(task[4]),
        }

    @classmethod
    def execute(cls, task, timeout):
        logs.debug(f'{cls.__name__} is executing {task}')
        kwargs = cls.map_kwargs(task)
        ftp = ftplib.FTP()
        ftp.connect(kwargs['host'], kwargs['port'])
        try:
            ftp.login(kwargs['user'], kwargs['passwd'])
        except ftplib.error_perm:
            return False
        else:
            return True
        finally:
            ftp.close()
