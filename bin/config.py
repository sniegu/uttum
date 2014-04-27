from os import path

class Folder(object):
    name = ''
    notify = True
    color = '#cb4b16'
    shortcut = None
    account = None

    IGNORE = ('name', 'account')

    def __init__(self, name):
        self.name = name

    @property
    def real_shortcut(self):
        if self.shortcut is not None:
            return self.shortcut
        return '%s_%s' % (self.name, self.account.name)

    @property
    def fullpath(self):
        return path.join(self.account.fullpath, self.name)

    def __str__(self):
        return 'folder %s:%s' % (self.account.name, self.name)

class Account(object):

    def __init__(self, name):
        self.name = name
        self.folders = {}


    def folder(self, name, **kwargs):
        f = Folder(name)
        for k, v in kwargs.items():
            setattr(f, k, v)
        f.account = self

        self.folders.update({name: f})

    @property
    def fullpath(self):
        return path.join(config.mail_path, self.name)

    @property
    def mailcheck_path(self):
        return path.join(config.mailcheck_path, self.name)

    def __str__(self):
        return 'account %s' % self.name

        # return 'account: %s [%s]' % (self.name, ', '.join([f.name for f in self.folders]))

def account_wrapper(name):
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
