from os import path

def account_wrapper(name):
    from accounts import Account
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
