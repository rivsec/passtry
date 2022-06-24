from passtry import logs


class Protocol:

    port = None
    protocol = None
    registry = dict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registry[cls.protocol] = cls

    @classmethod
    def execute(cls, fid, task):
        raise NotImplementedError
