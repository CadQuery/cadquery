"""Keep the interpreter from crashing at exit when casadi and nlopt are both loaded.

casadi and nlopt are SWIG-generated extension modules, and on Windows their PyPI
wheels are built against different C runtimes (nlopt: MSVC/UCRT; casadi: MinGW-w64
on the legacy msvcrt). SWIG modules in one process share a runtime type table
through the ``swig_runtime_data<N>.type_pointer_capsule`` capsule; at interpreter
exit the capsule's destructor walks the shared table and frees every module's
records with the C runtime of whichever module created the capsule. Freeing memory
that the other runtime allocated corrupts the heap (#1911: exit 0xC0000005 or
0xC0000374, after all output). Leaving those few records unfreed at exit is
harmless, so this disarms the destructor once both modules are present.
"""

import atexit
import ctypes
import sys


def _real(name: str) -> bool:
    module = sys.modules.get(name)
    return module is not None and getattr(module, "__file__", None) is not None


def disarm_swig_runtime_capsule() -> bool:
    """Clear the SWIG runtime capsule's destructor if casadi and nlopt are both loaded.

    Returns True if a capsule was disarmed. Safe to call more than once.
    """

    if not (_real("casadi") and _real("nlopt")):
        return False
    setter = ctypes.pythonapi.PyCapsule_SetDestructor
    setter.argtypes = [ctypes.py_object, ctypes.c_void_p]
    setter.restype = ctypes.c_int
    disarmed = False
    for name, module in list(sys.modules.items()):
        if name.startswith("swig_runtime_data"):
            capsule = getattr(module, "type_pointer_capsule", None)
            if capsule is not None and setter(capsule, None) == 0:
                disarmed = True
    return disarmed


atexit.register(disarm_swig_runtime_capsule)
