from __future__ import print_function, absolute_import

from os import path, mkdir, walk, remove
from . import utils
from .config import uttumrc, Folder
from . import filtering
from mailbox import Maildir, MaildirMessage
import shutil


def sync_folder(folder):
    uttumrc.offlineimap(['-a', folder.account.name, '-f', folder.name])


def sync(account):

    uttumrc.offlineimap(['-a', account.name])

    filtering.filter(account, 'INBOX')
    filtering.filter(account, 'INBOX', kind='cur')


def fetch(account):

    sync_folder(account.folders['INBOX'])

    filtering.filter(account, 'INBOX')
    filtering.filter(account, 'INBOX', kind='cur')


def create_folder(account, folder_name):
    print('creating folder %s for account %s' % (folder_name, account))
    sync(account)

    folder = Folder(account, folder_name)
    maildir = Maildir(folder.mailpath, create=True)
    message = MaildirMessage()
    message.set_payload('dummy message')
    maildir.add(message)

    sync_folder(folder)

    sync_folder(folder)

    shutil.rmtree(folder.mailpath)

    for root, dirs, files in walk(uttumrc.offlineimaprc_path.value):
        for f in files:
            if f == folder_name:
                full = path.join(root, f)
                print('removing %s' % full)
                remove(full)

    sync_folder(folder)


def check():
    utils.notify('checking mail...')
    try:
        for a in uttumrc.accounts.values():
            fetch(a)
    except:
        utils.notify('...failed to check mail', 1)

    utils.notify('...mail checked')


def check_bg():
    uttumrc.uttum(['--check'], devnull=True, async=True)

