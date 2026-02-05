from functools import wraps, update_wrapper
from inspect import signature, isbuiltin, currentframe
from typing import TypeVar, Callable, cast, TYPE_CHECKING, Any
from runtype import isa
from warnings import warn
from collections import UserDict

from multimethod import (
    multidispatch as _multidispatch,
    DispatchError,
    RETURN,
)


if TYPE_CHECKING:
    from typing import overload as multidispatch, overload as multimethod

    mypyclassmethod = classmethod

else:

    mypyclassmethod = lambda x: x

    from multimethod import multimethod

    class multidispatch(_multidispatch):
        """
        Multidispatch without register.
        """

        def __new__(cls, func):

            homonym = currentframe().f_back.f_locals.get(func.__name__)  # type: ignore
            if isinstance(homonym, multimethod):
                return homonym

            self = update_wrapper(dict.__new__(cls), func)
            self.pending = set()
            self.generics = []
            self.signatures = {}

            return self

        def __init__(self, func: Callable[..., RETURN]) -> None:
            if () not in self:
                self[()] = func
            else:
                self.register(func)


TCallable = TypeVar("TCallable", bound=Callable)


class deprecate_kwarg:
    def __init__(self, name, new_value):

        self.name = name
        self.new_value = new_value

    def __call__(self, f: TCallable) -> TCallable:
        @wraps(f)
        def wrapped(*args, **kwargs):

            f_sig_bound = signature(f).bind(*args, **kwargs)

            if self.name not in f_sig_bound.kwargs:
                warn(
                    f"Default value of {self.name} will change in the next release to {self.new_value}",
                    FutureWarning,
                )

            return f(*args, **kwargs)

        return cast(TCallable, wrapped)


class deprecate:
    def __call__(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):

            warn(f"{f.__name__} will be removed in the next release.", FutureWarning)

            return f(*args, **kwargs)

        return wrapped


# class cqmultimethod(multimethod):
#     def __call__(self, *args, **kwargs):

#         try:
#             return super().__call__(*args, **kwargs)
#         except DispatchError:
#             return next(iter(self.values()))(*args, **kwargs)


class deprecate_kwarg_name:
    def __init__(self, name, new_name):

        self.name = name
        self.new_name = new_name

    def __call__(self, f: TCallable) -> TCallable:
        @wraps(f)
        def wrapped(*args, **kwargs):

            if self.name in kwargs:
                warn(
                    f"Kwarg <{self.name}> will be removed. Please use <{self.new_name}>",
                    FutureWarning,
                )

            return f(*args, **kwargs)

        return cast(TCallable, wrapped)


def get_arity(f: TCallable) -> int:

    if isbuiltin(f):
        rv = 0  # assume 0 arity for builtins; they cannot be introspected
    else:
        # NB: this is not understood by mypy
        n_defaults = len(f.__defaults__) if f.__defaults__ else 0
        rv = f.__code__.co_argcount - n_defaults

    return rv


K = TypeVar("K")
V = TypeVar("V")


class BiDict(UserDict[K, V]):
    """
    Bi-directional dictionary.
    """

    _inv: dict[V, list[K]]

    def __init__(self, *args, **kwargs):

        self._inv = {}

        super().__init__(*args, **kwargs)

    def __setitem__(self, k: K, v: V):

        super().__setitem__(k, v)

        if v in self._inv:
            self._inv[v].append(k)
        else:
            self._inv[v] = [k]

    @property
    def inv(self) -> dict[V, list[K]]:

        return self._inv

    def clear(self):

        super().clear()
        self._inv.clear()

    def __delitem__(self, k: K):

        v = self.data.pop(k)

        # if needed in one-many cases
        if v in self._inv:
            # remove the inverse mapping
            inv = self._inv[v]
            inv.remove(k)

            # if needed remove the item completely
            if not inv:
                del self._inv[v]


def instance_of(obj: object, *args: object) -> bool:
    """
    Replacement for the instance_of method of typish, which
    now uses the isa method of the runtype package.
    """
    return isa(obj, cast(tuple[type[Any], ...], args))
