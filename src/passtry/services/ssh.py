import paramiko

from passtry import (
    logs,
    services,
)


class SSH(services.Service):

    port = 22
    service = 'ssh'
    timeout = 20

    @classmethod
    def map_kwargs(cls, task):
        return {
            'hostname': task[3],
            'username': task[1],
            'password': task[2],
            'port': int(task[4]),
        }

    @classmethod
    def execute(cls, task):
        logs.debug(f'{cls.__name__} is executing {task}')
        kwargs = cls.map_kwargs(task)
        transport = paramiko.Transport((kwargs['hostname'], kwargs['port']))
        try:
            transport.start_client()
        except paramiko.ssh_exception.SSHException as exc:
            logs.debug(f'{cls.__name__} connection failed (timed out?) for {task}')
            return None
        try:
            transport.auth_password(kwargs['username'], kwargs['password'], fallback=False)
        except paramiko.ssh_exception.AuthenticationException:
            return False
        else:
            return True
        finally:
            transport.close()
