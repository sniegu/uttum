from __future__ import print_function, absolute_import

from os import path, mkdir
from . import utils
from .config import uttumrc, Folder
from . import filtering
from contextlib import contextmanager
from mailbox import Maildir, MaildirMessage
import shutil


def unlocked_sync_folder(folder):
    uttumrc.offlineimap(['-a', folder.account.name, '-f', folder.name])


def unlocked_sync(account):

    uttumrc.offlineimap(['-a', account.name])

    filtering.filter(account)
    filtering.filter(account, kind='cur')

@contextmanager
def locked_account(account, timeout=5):
    with utils.locked_file(uttumrc.mail_path / ('.%s-sync.lock' % account.name), timeout=5):
        yield


def sync(account):
    with locked_account(account, timeout=5):
        unlocked_sync(account)

def create_folder(account, folder_name):
    with locked_account(account, timeout=5):
        print('creating folder %s for account %s' % (folder_name, account))
        unlocked_sync(account)

        folder = Folder(account, folder_name)
        maildir = Maildir(folder.mailpath, create=True)
        message = MaildirMessage()
        message.set_payload('dummy message')
        maildir.add(message)

        unlocked_sync_folder(folder)

        unlocked_sync_folder(folder)

        shutil.rmtree(folder.mailpath)
        shutil.rmtree(folder.mailpath)
        # Repository-psnc-remote/FolderValidity/newdir2
        # Account-psnc/LocalStatus-sqlite/newdir2

        # unlocked_sync(account)

        # unlocked_sync(account)




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

