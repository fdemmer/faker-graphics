import importlib

options = ["cairo", "cairocffi"]

for option in options:
    try:
        cairo = importlib.import_module(option)
        break
    except ImportError:
        pass
else:
    raise ImportError("Install either 'cairo' or 'cairocffi'.")

try:
    from enum import StrEnum, auto
except ImportError:
    from enum import auto  # noqa: F401

    from strenum import StrEnum  # noqa: F401
