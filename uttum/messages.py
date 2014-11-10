from __future__ import print_function, absolute_import

from os import path
import os
from .config import uttumrc, debug
from psutil import pid_exists
import shutil

class Message(object):

    def __init__(self, name):
        self.name = name
        self.message_path = path.join(uttumrc.queue_path, self.name)
        self.content_file = path.join(self.message_path, 'content')
        self.arguments_file = path.join(self.message_path, 'arguments')
        self.pid_file = path.join(self.message_path, 'pid')
        self.arguments = None


    def read(self):
        with open(self.arguments_file, 'r') as f:
            self.arguments = [argument.rstrip('\n') for argument in f.readlines()]


    def write(self, arguments, content):
        os.makedirs(self.message_path)
        self.arguments = arguments

        with open(self.content_file, 'wb') as f:
            f.write(content)

        with open(self.arguments_file, 'w') as f:
            f.write('\n'.join(self.arguments))


    def forget(self):
        shutil.rmtree(self.message_path)

    def pid(self):
        if not path.exists(self.pid_file):
            return None

        with open(self.pid_file, 'r') as p:
            pid = int(p.read())

        if pid_exists(pid):
            return pid
        else:
            debug('already dead: %s' % pid)
            os.remove(self.pid_file)
            return None

    def __str__(self):
        if not self.arguments:
            return self.name
        return self.name + ' : ' + self.arguments[self.arguments.index('--') + 1]

    @staticmethod
    def list_all():
        for msg_path in uttumrc.queue_path:
            yield Message(os.path.split(msg_path)[1])
