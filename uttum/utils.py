from __future__ import print_function, absolute_import

from contextlib import contextmanager
import signal
import fcntl
import os
from os import path

import subprocess

class RequirementNotSatisfied(Exception):
    pass

class CommonRequirementWrapper(object):

    def __init__(self, requirement, instance):
        self.instance = instance
        self.requirement = requirement

    @property
    def value_silent(self):
        return self.requirement._get_value(self.instance)

    @property
    def enabled(self):
        return self.value_silent is not None

    @property
    def value(self):
        self.raise_for_ok()
        return self.value_silent

    @property
    def name(self):
        return self.requirement.name

    def __str__(self):
        return (self.value_silent if self.value_silent is not None else '<none>')

    __unicode__ = __str__
    __repr__ = __str__


    def __bool__(self):
        return self.ok

    @property
    def ok(self):
        return self.requirement._is_ok(self.instance)

    def raise_for_ok(self):
        if not self.ok:
            raise RequirementNotSatisfied('%s is not properly configured: %s' % (self.name, self.value_silent))

    def try_resolve(self):
        return self.requirement.failure_comment

    def try_resolve_if_needed(self):
        if self.enabled and not self.ok:
            return self.try_resolve()
        return None

    def _reset_ok(self):
        self.requirement._reset_ok(self.instance)



class CommonRequirement(object):

    all_requirements = []

    def __init__(self, name, default_value=None, failure_comment='no information available'):
        self.name = name
        self.default_value = self._set_transform(default_value)
        self.all_requirements.append(self)
        self.failure_comment = failure_comment

    def _set_transform(self, value):
        return value

    def _get_ok(self, instance):
        return getattr(instance, '_%s_ok' % self.name, None)

    def _set_ok(self, instance, ok):
        setattr(instance, '_%s_ok' % self.name, ok)

    def _reset_ok(self, instance):
        self._set_ok(instance, None)


    def _get_value(self, instance):
        n = '_%s_value' % self.name
        if not hasattr(instance, n):
            setattr(instance, n, self.default_value)
        return getattr(instance, n)

    def _set_value(self, instance, value):
        return setattr(instance, '_%s_value' % self.name, self._set_transform(value))

    def __set__(self, instance, value):
        self._reset_ok(instance)
        self._set_value(instance, value)

    def __get__(self, instance, owner):
        return self.wrapper_class(self, instance)

    def _compute_ok(self, value):
        raise NotImplementedError()

    def _is_ok(self, instance):
        ok = self._get_ok(instance)
        if ok is None:
            value = self._get_value(instance)
            if value is None:
                ok = False
            else:
                ok = self._compute_ok(value)
            self._set_ok(instance, ok)

        return ok




class ProgramRequirementWrapper(CommonRequirementWrapper):


    def _to_run(self, command):
        return [self.value] + list(command)


    def __call__(self, command=[], silent=False, throw=False, lines=False, devnull=False, async=False, *args, **kwargs):

        if silent:
            if not self.ok:
                return False
        else:
            self.raise_for_ok()

        try:
            if lines:
                return subprocess.check_output(self._to_run(command), *args, **kwargs).decode().split('\n')
            else:
                if devnull:
                    dn = open('/dev/null', 'w')
                    kwargs['stdout'] = dn
                    kwargs['stderr'] = dn

                if async:
                    subprocess.Popen(self._to_run(command), *args, **kwargs)
                else:
                    subprocess.check_call(self._to_run(command), *args, **kwargs)

                return True

        except Exception as e:
            print('failed to call %s: %s' % (self.requirement.name, e))
            if throw:
                raise
            if lines:
                return []
            else:
                return False


class ProgramRequirement(CommonRequirement):

    wrapper_class = ProgramRequirementWrapper

    def __init__(self, name, default_value=None, failure_comment=None, *args, **kwargs):
        if default_value is None:
            default_value = name
        if failure_comment is None:
            failure_comment = 'install package providing %s program' % name
        super(ProgramRequirement, self).__init__(name, default_value=default_value, failure_comment=failure_comment, *args, **kwargs)

    def _compute_ok(self, value):
        try:
            subprocess.check_call(['which', value], stdout=open('/dev/null', 'w'))
            return True
        except subprocess.CalledProcessError as e:
            return False



class FilePathRequirementWrapper(CommonRequirementWrapper):
    pass

class FileRequirementWrapper(FilePathRequirementWrapper):

    def try_resolve(self):
        if self.requirement.template is None:
            return self.requirement.failure_comment

        filename = self.value_silent
        if path.exists(filename):
            raise Exception('file already exists')

        assure_path(path.dirname(filename))
        print('creating file: %s' % filename)
        with open(filename, 'w') as f:
            f.write(self.requirement.template)

        subprocess.check_call([path.expandvars('$EDITOR'), filename])

        return 'created file: %s' % filename



class PathRequirementWrapper(FilePathRequirementWrapper):

    def __div__(self, other):
        return path.join(self.value_silent, other)

    __truediv__ = __div__

    def __iter__(self):
        self.raise_for_ok()
        return os.listdir(self.value).__iter__()

    def try_resolve(self):
        assure_path(self.value_silent)
        self._reset_ok()
        return 'created directory: %s' % self.value_silent


class FilePathRequirement(CommonRequirement):

    def _set_transform(self, value):
        return path.expanduser(value) if value is not None else None

    def _compute_ok(self, value):
        return path.exists(value)

class FileRequirement(FilePathRequirement):

    wrapper_class = FileRequirementWrapper

    def __init__(self, name, template=None, *args, **kwargs):
        super(FileRequirement, self).__init__(name, *args, **kwargs)
        self.template = template



class PathRequirement(FilePathRequirement):

    wrapper_class = PathRequirementWrapper



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


def assure_path(p):
    if not path.exists(p):
        os.makedirs(p)

def write_file(filename):
    assure_path(path.dirname(filename))
    return open(filename, 'w')
