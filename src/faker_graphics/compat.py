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
