class Service:

    port = None
    service = None
    registry = dict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registry[cls.service] = cls

    @classmethod
    def execute(cls, task, timeout):
        raise NotImplementedError
