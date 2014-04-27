from os import path
from config import config

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

