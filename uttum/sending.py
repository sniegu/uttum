from __future__ import print_function, absolute_import

from uuid import uuid4
import sys
from .messages import OutgoingMessage
from .config import debug, uttumrc
from . import utils
from time import sleep
import os
import signal

def status(message):
    message.read()
    print("%s : %s" % (message, 'frozen' if message.pid() else 'dormant'))


class Wrapper(object):
    def __init__(self, value):
        self.value = value

def abort():
    aborted = 0
    for msg in OutgoingMessage.list_all():
        msg.read()
        pid = msg.pid()
        if pid:
            os.kill(int(pid), signal.SIGUSR1)
            aborted = aborted + 1
            debug('abort: %s' % pid)

    if aborted:
        utils.notify("aborted messages: %d" % aborted)


def send(message):
    message.read()

    with open(message.content_file, 'r') as content:
        debug('sending: %s' % message)
        if not uttumrc.msmtp(message.arguments, stdin=content, throw=False):
            utils.notify("failed to send: %s" % message, 1)
            return False

        utils.notify("sent: %s" % message)
        message.forget()
        return True


def freeze(message):
    message.read()
    debug("starting sleep")
    aborted = Wrapper(False)

    def stop_handler(signum, frame):
        debug("stoping sleep")
        aborted.value = True

    with utils.signal_handler(signal.SIGUSR1, stop_handler):
        with utils.scoped_file(message.pid_file, str(os.getpid())):
            sleep(uttumrc.freeze_time)

    if aborted.value:
        debug("was aborted: %s" % message)
    else:
        send(message)



def queue(arguments):

    message = OutgoingMessage(str(uuid4()))
    message.write(arguments, sys.stdin.buffer.read())

    uttumrc.uttum(['--freeze', '--message', message.name], async_mode=True)
