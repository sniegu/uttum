from __future__ import print_function, absolute_import

from . import utils
import locale
import re
from .messages import OutgoingMessage
from .config import uttumrc

MAIL_MATCHER = re.compile(r'You\ have\ (\d+)\ new\ (?:and\ (?:\d+)\ unread\ )?messages\ in\ /home/\w+/\.mail/.*/(.*)')

def add(out, text, name, color='#cb4b16'):
    out.append(dict(color=color, name=name, full_text=text))

# TODO: this is to be removed and to make a real status
def check_all():

    out = []

    if not uttumrc.mailcheck:
        add(out, 'missing mailcheck program')
        return out

    if uttumrc.sentry_path.invalid:
        add(out, 'sentry file not available')
        return out

    for account in uttumrc.accounts:
        for m in uttumrc.mailcheck(['-c', '-f', account.mailcheckrc.value], lines=True):
            match = MAIL_MATCHER.match(m)
            if match:
                folder_name = match.group(2)
                # if folder_name not in account.folders:
                #     continue
                folder = account.folder(folder_name)
                number = match.group(1)
                if folder.notify:
                    add(out, folder.alias + ': ' + number, folder.alias, color=folder.color)


    queued = sum(1 for _ in OutgoingMessage.list_all())
    if queued > 0:
        add(out, 'queued: %s' % queued, 'queued', '#6c71c4')
    return out





