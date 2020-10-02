import os
import os.path
import sys


class LockFile:

    def __init__(self, filename):
        self._filename = filename

    def __enter__(self):
        if os.path.isfile(self._filename):
            print("Another instance of this script is already running. Exiting...")
            sys.exit(0)

        with open(self._filename, "w") as f:
            f.write(str(os.getpid()))

    def __exit__(self, typ, value, traceback):
        os.remove(self._filename)
