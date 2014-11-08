from __future__ import print_function, absolute_import

from os import system
from subprocess import check_call, check_output, CalledProcessError, Popen, STDOUT
import sys
from os import path
import os
from uuid import uuid4
import signal
from time import sleep
import re
import locale

from .config import Config, config, debug
from .accounts import Account, Folder
from .messages import Message
from .parser import parser
from . import utils

command = parser.add

@command
def notify(line, good=0):
    good = int(good)
    Popen(['twmnc', '--content', line, '--fg', '#859900' if good == 0 else '#dc322f'])

@command
def filter(account, folder='INBOX', kind='new'):
    debug('filtering: %s %s %s' % (account.name, folder, kind))
    input_path = path.join(config.mail_path, account.name, folder, kind)
    debug('processing: %s' % input_path)

    for msg in os.listdir(input_path):
        msg_path = path.join(input_path, msg)
        if not path.exists(msg_path):
            continue

        failed = False
        try:
            with open(msg_path) as msg_file:
                check_call(['procmail', path.join(path.expanduser('~/.procmailrc'), account.name)], stdin=msg_file)
        except Exception as e:
            failed = True

        print('E' if failed else '.', end="")
        sys.stdout.flush()
        if failed:
            print('failed to process %s' % msg)
        else:
            os.rename(msg_path, path.join(config.mail_path, 'sorted', msg))

        try:
            check_call(['notify_i3status'])
        except Exception as e:
            print('failed to notify i3status')

    print("")


@command
def unlocked_sync(account):
    # debug ('offlineimap -a ')
    try:
        # -o -u quiet
        check_call(['offlineimap', '-a', account.name])
    except CalledProcessError as e:
        print('failed to call offlineimap: %s' % e)
        raise

    filter(account)
    filter(account, kind='cur')

@command
def sync(account):
    try:
        with utils.locked_file(path.join(config.mail_path, '.%s-sync.lock' % account.name)):
            unlocked_sync(account)

    except Exception as e:
        print('failed to lock: %s' % e)
        raise


@parser.simple_command
def status():
    for msg in Message.list_all():
        msg.read()
        print("%s : %s" % (msg, 'frozen' if msg.pid() else 'dormant'))


class Wrapper(object):
    def __init__(self, value):
        self.value = value

@parser.simple_command
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
        notify("aborted messages: %d" % aborted)


@command
def send(name):
    msg = Message(name)
    msg.read()
    try:
        with open(msg.content_file, 'r') as content:
            debug('sending: %s' % msg)
            check_call(['msmtp'] + msg.arguments, stdin=content)
            notify("sent: %s" % msg)
            msg.forget()

    except CalledProcessError as e:
        alert = "failed to send: %s" % ','.join(msg)
        print(alert)
        notify(alert, 1)
        sys.exit(1)


@command
def freeze(name):
    msg = Message(name)
    msg.read()
    debug("starting sleep")
    aborted = Wrapper(False)

    def stop_handler(signum, frame):
        debug("stoping sleep")
        aborted.value = True

    with utils.signal_handler(signal.SIGUSR1, stop_handler):
        with utils.scoped_file(msg.pid_file, str(os.getpid())):
            sleep(10)

    if aborted.value:
        debug("was aborted: %s" % msg)
    else:
        send(msg.name)



@parser.simple_command
def queue():

    msg = Message(str(uuid4()))
    msg.write(parser.unknown_args, sys.stdin.read())

    Popen(['uttum', 'freeze', msg.name])

# TODO: this is to be removed and to make a real status
@parser.simple_command
def check_all():
    mail_matcher = re.compile(r'You\ have\ (\d+)\ new\ (?:and\ (?:\d+)\ unread\ )?messages\ in\ /home/\w+/\.mail/.*/(.*)')
    encoding = locale.getdefaultlocale()[1]
    out = []

    def add(text, name, color='#cb4b16'):
        out.append(dict(color=color, name=name, full_text=text))

    for account in config.accounts.values():
        try:
            mail = check_output(['mailcheck', '-c', '-f', account.mailcheck_path]).decode().split('\n')
            for m in mail:
                match = mail_matcher.match(m)
                if match:
                    folder_name = match.group(2)
                    if folder_name not in account.folders:
                        continue
                    folder = account.folders[folder_name]
                    number = match.group(1)
                    if folder.notify:
                        add(folder.name + ': ' + number, folder.name, color=folder.color)

        except CalledProcessError:
            pass

    queued = sum(1 for _ in Message.list_all())
    if queued > 0:
        add('queued: %s' % queued, 'queued', '#6c71c4')
    return out


@parser.simple_command
def check():
    notify('checking mail...')
    try:
        for a in config.accounts.values():
            sync(a)
    except:
        notify('...failed to check mail', 1)
        raise

    notify('...mail checked')


@parser.simple_command
def check_bg():
    Popen(['uttum', 'check'], stdout=open('/dev/null', 'w'), stderr=STDOUT)


@parser.simple_command
def show():
    for k, v in config.__dict__.items():
        print('%s = %s' % (k, v))

    for a in config.accounts.values():
        print('* account: %s' % a.name)
        for f in a.folders.values():
            print('    * folder: %s' % f.name)
            for k, v in f.__dict__.items():
                if k not in Folder.IGNORE:
                    print('        * %s: %s' % (k, v))

@parser.simple_command
def generate():
    for p in os.listdir(config.merged_path):
        f = path.join(config.merged_path, p)
        if not path.islink(f):
            raise Exception('file %s is not link' % f)
        os.remove(f)

    for a in config.accounts.values():
        print('syncing: %s' % a)
        with open(path.join(config.mutt_path, '%s_mailboxes' % a.name), 'w') as mutt_mailboxes_file:
            with open(a.mailcheck_path, 'w') as mailcheck_file:
                for f in a.folders.values():
                    print('syncing: %s' % f)
                    shortcut = f.real_shortcut
                    link_name = path.join(config.merged_path, shortcut)
                    source = f.fullpath

                    mutt_mailboxes_file.write('mailboxes +%s\n' % shortcut)
                    mailcheck_file.write('%s\n' % f.fullpath)

                    print('creating shortcut: %s -> %s' % (link_name, source))
                    os.symlink(source, link_name)
