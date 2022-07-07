import paramiko

from passtry import (
    exceptions,
    logs,
    services,
)


__all__ = ['Ssh']


class Ssh(services.Service):

    port = 22
    service = 'ssh'

    @classmethod
    def map_kwargs(cls, task):
        return {
            'hostname': task[2],
            'username': task[3],
            'password': task[4],
            'port': int(task[1]),
        }

    @classmethod
    def execute(cls, task, timeout):
        logs.logger.debug(f'{cls.__name__} is executing {task}')
        kwargs = cls.map_kwargs(task)
        try:
            transport = paramiko.Transport((kwargs['hostname'], kwargs['port']))
            transport.start_client(timeout=timeout)
        except paramiko.ssh_exception.SSHException:
            logs.logger.debug(f'{cls.__name__} connection failed (timed out?) for {task}')
            raise exceptions.ConnectionFailed
        try:
            transport.auth_password(kwargs['username'], kwargs['password'])
        except paramiko.ssh_exception.AuthenticationException:
            result = False
        else:
            result = True
        transport.close()
        return result
