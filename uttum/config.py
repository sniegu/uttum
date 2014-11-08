from __future__ import print_function, absolute_import

from os import path

debug = print

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

def load_config():

    filename = path.join(config.ttum_path, 'config')
    from six import exec_
    with open(filename, 'r') as f:
        exec_(f.read(), globals())

load_config()

def show():
    for k, v in config.__dict__.items():
        print('%s = %s' % (k, v))

    for a in config.accounts.values():
        print('* account: %s' % a.name)
        for f in a.folders.values():
            print('    * folder: %s' % f.name)
            for k, v in f.__dict__.items():
                if k not in Folder.IGNORE:
                    print('        * %s: %s' % (k, v))

def generate():
    for p in os.listdir(config.merged_path):
        f = path.join(config.merged_path, p)
        if not path.islink(f):
            raise Exception('file %s is not link' % f)
        os.remove(f)

    for a in config.accounts.values():
        print('syncing: %s' % a)
        with open(path.join(config.mutt_path, '%s_mailboxes' % a.name), 'w') as mutt_mailboxes_file:
            with open(a.mailcheck_path, 'w') as mailcheck_file:
                for f in a.folders.values():
                    print('syncing: %s' % f)
                    shortcut = f.real_shortcut
                    link_name = path.join(config.merged_path, shortcut)
                    source = f.fullpath

                    mutt_mailboxes_file.write('mailboxes +%s\n' % shortcut)
                    mailcheck_file.write('%s\n' % f.fullpath)

                    print('creating shortcut: %s -> %s' % (link_name, source))
                    os.symlink(source, link_name)
