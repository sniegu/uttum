from __future__ import print_function, absolute_import

from subprocess import check_call
from os import path, listdir
from . import config
from .config import debug
import sys
import os


def filter(account, folder='INBOX', kind='new'):

    if not account.procmailrc:
        return

    debug('filtering: %s %s %s' % (account.name, folder, kind))
    input_path = path.join(config.config.mail_path, account.name, folder, kind)
    debug('processing: %s' % input_path)

    for msg in listdir(input_path):
        msg_path = path.join(input_path, msg)
        if not path.exists(msg_path):
            continue

        failed = False
        try:
            with open(msg_path) as msg_file:
                check_call(['procmail', account.procmailrc], stdin=msg_file)
        except Exception as e:
            failed = True

        print('E' if failed else '.', end="")
        sys.stdout.flush()
        if failed:
            print('failed to process %s' % msg)
        else:
            os.rename(msg_path, path.join(config.config.mail_path, 'sorted', msg))

        try:
            check_call(['notify_i3status'])
        except Exception as e:
            print('failed to notify i3status')

    print("")

