from __future__ import print_function, absolute_import

from contextlib import contextmanager
import signal
import fcntl
import os

import subprocess

@contextmanager
def locked_file(filename):
    with open(filename, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


@contextmanager
def signal_handler(signum, handler):
    old_handler = signal.signal(signum, handler)
    try:
        yield
    finally:
        signal.signal(signum, old_handler )


@contextmanager
def scoped_file(filepath, content):
    with open(filepath, 'w') as f:
        f.write(content)
    try:
        yield
    finally:
        os.remove(filepath)

def notify(line, good=0):
    good = int(good)
    subprocess.Popen(['twmnc', '--content', line, '--fg', '#859900' if good == 0 else '#dc322f'])

