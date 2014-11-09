from __future__ import print_function, absolute_import

from . import utils
import locale
import re
from .messages import Message
from .config import uttumrc

MAIL_MATCHER = re.compile(r'You\ have\ (\d+)\ new\ (?:and\ (?:\d+)\ unread\ )?messages\ in\ /home/\w+/\.mail/.*/(.*)')

# TODO: this is to be removed and to make a real status
def check_all():

    if not uttumrc.mailcheck:
        return
    encoding = locale.getdefaultlocale()[1]
    out = []

    def add(text, name, color='#cb4b16'):
        out.append(dict(color=color, name=name, full_text=text))

    for account in uttumrc.accounts.values():
        for m in uttumrc.mailcheck.lines(['-c', '-f', account.mailcheckrc]):
            match = MAIL_MATCHER.match(m)
            if match:
                folder_name = match.group(2)
                if folder_name not in account.folders:
                    continue
                folder = account.folders[folder_name]
                number = match.group(1)
                if folder.notify:
                    add(folder.name + ': ' + number, folder.name, color=folder.color)


    queued = sum(1 for _ in Message.list_all())
    if queued > 0:
        add('queued: %s' % queued, 'queued', '#6c71c4')
    return out





