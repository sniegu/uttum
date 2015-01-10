from __future__ import print_function, absolute_import

from . import utils
import locale
import re
from .messages import OutgoingMessage
from .config import uttumrc

def add(out, text, name, color='#cb4b16'):
    out.append(dict(color=color, name=name, full_text=text))

# TODO: this is to be removed and to make a real status
def check_all():

    out = []


    if uttumrc.sentry_path.invalid:
        add(out, 'sentry file not available')
        return out

    for account in uttumrc.accounts:
        for folder in account.folders:
            if folder.notify:
                number = sum(1 for _ in folder.new_messages)
                if number > 0:
                    add(out, '%s: %s' % (folder.alias, number), folder.alias, color=folder.color)


    queued = sum(1 for _ in OutgoingMessage.list_all())
    if queued > 0:
        add(out, 'queued: %s' % queued, 'queued', '#6c71c4')
    return out





