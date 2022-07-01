import paramiko

from passtry import (
    exceptions,
    logs,
    services,
)


class SSH(services.Service):

    port = 22
    service = 'ssh'

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
        try:
            transport = paramiko.Transport((kwargs['hostname'], kwargs['port']))
            transport.start_client(timeout=timeout)
        except paramiko.ssh_exception.SSHException as exc:
            logs.debug(f'{cls.__name__} connection failed (timed out?) for {task}')
            raise exceptions.ConnectionFailed
        result = None
        try:
            transport.auth_password(kwargs['username'], kwargs['password'])
        except paramiko.ssh_exception.AuthenticationException:
            result = False
        else:
            result = True
        transport.close()
        return result
