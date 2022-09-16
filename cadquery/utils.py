from functools import wraps
from inspect import signature
from warnings import warn

from multimethod import multimethod, DispatchError


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
                    f"Default value of {self.name} will change in the next release to {self.new_value}",
                    FutureWarning,
                )

            return f(*args, **kwargs)

        return wrapped


class deprecate:
    def __call__(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):

            warn(f"{f.__name__} will be removed in the next release.", FutureWarning)

            return f(*args, **kwargs)

        return wrapped


class cqmultimethod(multimethod):
    def __call__(self, *args, **kwargs):

        try:
            return super().__call__(*args, **kwargs)
        except DispatchError:
            return next(iter(self.values()))(*args, **kwargs)


class deprecate_kwarg_name:
    def __init__(self, name, new_name):

        self.name = name
        self.new_name = new_name

    def __call__(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):

            f_sig_params = signature(f).parameters

            if f_sig_params[self.name]:
                warn(
                    f"Kwarg <{self.name}> will be removed. Please use <{self.new_name}>",
                    FutureWarning,
                )

            return f(*args, **kwargs)

        return wrapped
