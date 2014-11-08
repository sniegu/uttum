from __future__ import print_function, absolute_import

from os import path

debug = print

def account_wrapper(name):
    from uttum.accounts import Account
    account = Account(name)
    config.accounts.update({name: account})
    return account


class Config(object):
    def __init__(self):
        self.ttum_path = path.expanduser('~/.ttum')
        self.queue_path = path.join(self.ttum_path, 'queue')
        self.mail_path = path.expanduser('~/.mail')
        self.mutt_path = path.expanduser('~/.mutt')
        self.merged_path = path.join(self.mail_path, 'merged')
        self.mailcheck_path = path.expanduser('~/.mailcheckrc')
        self.accounts = {}
        self.Account = account_wrapper

config = Config()

def load_config():

    filename = path.join(config.ttum_path, 'config')
    from six import exec_
    with open(filename, 'r') as f:
        exec_(f.read(), globals())

load_config()
