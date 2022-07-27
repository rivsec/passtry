import ftplib
import socket

from passtry import (
    exceptions,
    logs,
    services,
)


__all__ = ['Ftp']


class Ftp(services.Service):

    port = 21
    service = 'ftp'

    @classmethod
    def map_kwargs(cls, task):
        return {
            'host': task[2],
            'user': task[3],
            'passwd': task[4],
            'port': int(task[1]),
        }

    @classmethod
    def execute(cls, task, timeout):
        kwargs = cls.map_kwargs(task)
        ftp = ftplib.FTP(timeout=timeout)
        try:
            ftp.connect(kwargs['host'], kwargs['port'])
        except (TimeoutError, ConnectionRefusedError, EOFError):
            raise exceptions.ConnectionFailed
        result = False
        try:
            ftp.login(kwargs['user'], kwargs['passwd'])
        except ftplib.error_perm:
            result = False
        # NOTE: Repeating handling `TimeoutError` exception on purpose.
        except (TimeoutError, EOFError, socket.timeout):
            raise exceptions.ConnectionFailed
        else:
            result = True
        finally:
            try:
                ftp.quit()
            except (OSError, EOFError):
                pass
        return result
