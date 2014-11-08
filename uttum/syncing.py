from __future__ import print_function, absolute_import
from subprocess import check_call, CalledProcessError, Popen

from os import path
from . import utils
from . import config
from . import filtering

def unlocked_sync(account):
    # debug ('offlineimap -a ')
    try:
        # -o -u quiet
        check_call(['offlineimap', '-a', account.name])
    except CalledProcessError as e:
        print('failed to call offlineimap: %s' % e)
        raise

    filtering.filter(account)
    filtering.filter(account, kind='cur')


def sync(account):
    try:
        with utils.locked_file(path.join(config.config.mail_path, '.%s-sync.lock' % account.name)):
            unlocked_sync(account)

    except Exception as e:
        print('failed to lock: %s' % e)
        raise

def check():
    utils.notify('checking mail...')
    try:
        for a in config.config.accounts.values():
            sync(a)
    except:
        utils.notify('...failed to check mail', 1)
        raise

    utils.notify('...mail checked')


def check_bg():
    Popen(['uttum', '--check'], stdout=open('/dev/null', 'w'), stderr=STDOUT)

