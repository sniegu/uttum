from __future__ import print_function, absolute_import

from contextlib import contextmanager
import signal
import fcntl
import os
from os import path

import subprocess

# class BoundCall(object):

#     def __init__(self, requirement, command, args, kwargs):
#         self.requirement = requirement
#         self.command = [self.requirement.value] + list(command)
#         self.args = args
#         self.kwargs = kwargs

#     def async(self):
#         subprocess.Popen(self.command, *self.args, **self.kwargs)

#     def run(self):
#         subprocess.check_call(self.command, *self.args, **self.kwargs)


class RequirementWrapper(object):

    def __init__(self, requirement):
        self.requirement = requirement

    # def __call__(self, command, *args, **kwargs):
    #     self.requirement.raise_for_ok()
    #     return BoundCall(self.requirement, command, args, kwargs)

    def call(self, command=[], silent=False, throw=False, lines=False, *args, **kwargs):

        if silent and not self.requirement.ok:
            return False

        self.requirement.raise_for_ok()

        try:
            to_run = [self.requirement.value] + list(command)
            if lines:
                subprocess.check_call(to_run, *args, **kwargs)
                return True
            else:
                return subprocess.check_output(to_run, *args, **kwargs).decode().split('\n')

        except Exception as e:
            print('failed to call %s: %s' % (self.requirement.name, e))
            if throw:
                raise
            if lines:
                return []
            else:
                return False


    def popen(self, command=[], *args, **kwargs):
        self.requirement.raise_for_ok()
        return subprocess.Popen(command, *args, **kwargs)


    @property
    def ok(self):
        return self.requirement.is_ok()

    @property
    def name(self):
        return self.requirement.name



    def __str__(self):
        return (self.requirement.value if self.requirement.value is not None else '<none>')

    __unicode__ = __str__
    __repr__ = __str__


    def __bool__(self):
        return self.requirement.is_ok()


class RequirementNotSatisfied(Exception):
    pass

class Requirement(object):

    def __init__(self, name, value=None):
        self.name = name
        self.value = value if value is not None else name
        self._ok = None


    def __set__(self, instance, value):
        self._ok = None
        self.value = value

    def is_ok(self):
        if self._ok is None:
            if self.value is None:
                self._ok = False
            else:
                try:
                    subprocess.check_call(['which', self.value], stdout=open('/dev/null', 'w'))
                    self._ok = True
                except subprocess.CalledProcessError as e:
                    self._ok = False

        return self._ok

    def raise_for_ok(self):
        if not self.is_ok():
            raise RequirementNotSatisfied('%s is not properly configured: %s' % (self.name, self.value))

    def __get__(self, instance, owner):
        return RequirementWrapper(self)



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

