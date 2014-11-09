from __future__ import print_function, absolute_import

from os import path, listdir
from .config import debug, config
import sys
import os


def filter(account, folder='INBOX', kind='new'):

    if not config.procmail or not account.procmailrc:
        return

    debug('filtering: %s %s %s' % (account.name, folder, kind))
    input_path = path.join(config.mail_path, account.name, folder, kind)
    debug('processing: %s' % input_path)

    for msg in listdir(input_path):
        msg_path = path.join(input_path, msg)
        if not path.exists(msg_path):
            continue

        failed = False
        with open(msg_path) as msg_file:
            if not config.procmail.call([account.procmailrc], stdin=msg_file, throw=False):
                failed = True

        print('E' if failed else '.', end="")
        sys.stdout.flush()
        if failed:
            print('failed to process %s' % msg)
        else:
            os.rename(msg_path, path.join(config.mail_path, 'sorted', msg))

        config.notify_i3status.call(silent=True, throw=False)

    print("")

