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
    def execute(cls, fid, task):
        logs.debug(f'{cls.__name__} is executing {fid}')
        kwargs = cls.map_kwargs(task)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
        try:
            client.connect(
                kwargs.pop('hostname'),
                allow_agent=False,
                look_for_keys=False,
                timeout=cls.timeout,
                banner_timeout=cls.timeout,
                auth_timeout=cls.timeout,
                **kwargs
            )
        except paramiko.ssh_exception.AuthenticationException:
            logs.debug(f'{cls.__name__} authentication failed for {task}')
            return None
        except paramiko.ssh_exception.NoValidConnectionsError:
            logs.debug(f'{cls.__name__} connection failed for {task}')
            return None
        except (paramiko.ssh_exception.SSHException, EOFError):
            logs.debug(f'{cls.__name__} connection failed (timed out?) for {task}')
            return None
        except Exception as exc:
            logs.debug(f'{cls.__name__} connection failed with {exc} for {task}')
            return None
        else:
            client.close()
            logs.debug(f'{cls.__name__} authentication succeeded for {task}')
            return task
