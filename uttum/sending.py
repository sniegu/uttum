from __future__ import print_function, absolute_import

from subprocess import check_call, CalledProcessError, Popen
from uuid import uuid4
import sys
from .messages import Message
from .config import debug
from . import utils

def status(message):
    message.read()
    print("%s : %s" % (message, 'frozen' if message.pid() else 'dormant'))


class Wrapper(object):
    def __init__(self, value):
        self.value = value

def abort():
    aborted = 0
    for msg in Message.list_all():
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
    try:
        with open(message.content_file, 'r') as content:
            debug('sending: %s' % message)
            check_call(['msmtp'] + message.arguments, stdin=content)
            utils.notify("sent: %s" % message)
            message.forget()

    except CalledProcessError as e:
        alert = "failed to send: %s" % ','.join(message)
        print(alert)
        utils.notify(alert, 1)
        sys.exit(1)


def freeze(message):
    message.read()
    debug("starting sleep")
    aborted = Wrapper(False)

    def stop_handler(signum, frame):
        debug("stoping sleep")
        aborted.value = True

    with utils.signal_handler(signal.SIGUSR1, stop_handler):
        with utils.scoped_file(message.pid_file, str(os.getpid())):
            sleep(10)

    if aborted.value:
        debug("was aborted: %s" % message)
    else:
        send(message)



def queue(arguments):

    message = Message(str(uuid4()))
    message.write(arguments, sys.stdin.read())

    Popen(['uttum', '--freeze', '--message', message.name])
