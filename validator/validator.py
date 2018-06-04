import importlib
import inspect
import sys

m = importlib.import_module("function-server.main")


def main():
    f = m.import_function(sys.argv[1], sys.argv[2])

    num_args = len(inspect.getfullargspec(f)[0])
    if (num_args != 2):
        raise TypeError("Handler should accept 2 arguments, but has %s argument(s)" % num_args)


if __name__ == "__main__":
    main()
