from functools import wraps
from inspect import signature
from warnings import warn


class deprecate_kwarg:
    def __init__(self, name, new_value):

        self.name = name
        self.new_value = new_value

    def __call__(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):

            f_sig_bound = signature(f).bind(*args, **kwargs)

            if self.name not in f_sig_bound.kwargs:
                warn(
                    f"Default walue of {self.name} will change in the next relase to {self.new_value}",
                    FutureWarning,
                )

            return f(*args, **kwargs)

        return wrapped


class deprecate:
    def __call__(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):

            warn(f"{f.__name__} will be removed in the next relase.", FutureWarning)

            return f(*args, **kwargs)

        return wrapped
