from __future__ import print_function, absolute_import

from os import path, listdir
from .config import debug, uttumrc, Message
import sys
import os
from . import predicates



def filter(folder, kind='new'):


    input_path = path.join(folder.mailpath, kind)
    debug('processing: %s' % input_path)

    for msg in listdir(input_path):
        msg_path = path.join(input_path, msg)
        if not path.exists(msg_path):
            continue
        message = Message.from_file(folder, msg_path)

        # print('processing message: %s' % msg)

        context = predicates.Context(message)
        for rule in folder.account.rules:
            if rule.predicate.matches(context):
                # print('rule %s matches' % (rule.predicate))
                rule.action(message)
                break
        else:
            if not uttumrc.procmail or not folder.account.procmailrc:
                continue
            print('trying to use procmail')


            with open(msg_path) as msg_file:
                if uttumrc.procmail([folder.account.procmailrc.value], stdin=msg_file, throw=False):
                    print('.', end="")
                    os.rename(msg_path, path.join(uttumrc.mail_path.value, 'sorted', msg))
                else:
                    print('E', end="")
                    print('failed to process %s' % msg)

        sys.stdout.flush()


