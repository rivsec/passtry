import paramiko

from passtry import (
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
            'port': task[4],
        }

    @classmethod
    def execute(cls, fid, task):
        logs.debug(f'{cls.__name__} is executing {fid}')
        kwargs = cls.map_kwargs(task)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
        try:
            client.connect(kwargs.pop('hostname'), **kwargs)
        except paramiko.ssh_exception.AuthenticationException:
            logs.debug(f'{cls.__name__} authentication failed for {task}')
            return None
        else:
            logs.debug(f'{cls.__name__} authentication succeeded for {task}')
            return task
