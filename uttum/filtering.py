from __future__ import print_function, absolute_import

from os import path, listdir
from .config import debug, uttumrc
import sys
import os



def filter(account, folder='INBOX', kind='new'):


    input_path = account.mailpath / ('%s/%s' % (folder, kind))
    debug('processing: %s' % input_path)

    for msg in listdir(input_path):
        msg_path = path.join(input_path, msg)
        if not path.exists(msg_path):
            continue

        # print('processing message: %s' % msg)

        # for rule in account.rules:
        #     if rule.process(msg):
        #         print('rule %s matches' % (rule.predicate))
        #         break
        #     else:
        #         print('rule %s does not match' % (rule.predicate))
        # else:
        #     print('nothing matched')

        if not uttumrc.procmail or not account.procmailrc:
            continue

        with open(msg_path) as msg_file:
            if uttumrc.procmail([account.procmailrc.value], stdin=msg_file, throw=False):
                print('.', end="")
                os.rename(msg_path, path.join(uttumrc.mail_path.value, 'sorted', msg))
            else:
                print('E', end="")
                print('failed to process %s' % msg)

        sys.stdout.flush()

    print("")

