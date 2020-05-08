import sys
from threading import Lock


def import_string(import_name):
    import_name = str(import_name).replace(":", ".")
    try:
        __import__(import_name)
    except (ImportError, ModuleNotFoundError):
        if "." not in import_name:
            raise
    else:
        return sys.modules[import_name]

    module_name, obj_name = import_name.rsplit(".", 1)
    try:
        module = __import__(module_name, None, None, [obj_name])
    except ModuleNotFoundError as e:
        raise ImportError(e)

    try:
        return getattr(module, obj_name)
    except AttributeError as e:
        raise ImportError(e)


class cached_property:
    """ thread safe cached property """

    def __init__(self, func, name=None):
        self.func = func
        self.__doc__ = getattr(func, "__doc__")
        self.name = name or func.__name__
        self.lock = Lock()

    def __get__(self, instance, cls=None):
        with self.lock:
            if instance is None:
                return self
            try:
                return instance.__dict__[self.name]
            except KeyError:
                res = instance.__dict__[self.name] = self.func(instance)
                return res


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
