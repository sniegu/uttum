from __future__ import print_function, absolute_import

from os import path
from . import utils
from .config import uttumrc
from . import filtering

def unlocked_sync(account):

    uttumrc.offlineimap(['-a', account.name])

    filtering.filter(account)
    filtering.filter(account, kind='cur')


def sync(account):
    with utils.locked_file(uttumrc.mail_path / ('.%s-sync.lock' % account.name), timeout=5):
        unlocked_sync(account)


def check():
    utils.notify('checking mail...')
    try:
        for a in uttumrc.accounts.values():
            sync(a)
    except:
        utils.notify('...failed to check mail', 1)

    utils.notify('...mail checked')


def check_bg():
    uttumrc.uttum(['--check'], devnull=True, async=True)

