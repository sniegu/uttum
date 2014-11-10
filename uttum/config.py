from __future__ import print_function, absolute_import

from os import path
import os
from .utils import ProgramRequirement, FileRequirement, PathRequirement, CommonRequirement, CommonRequirementWrapper
from . import utils

debug = print

class ConfigObject(object):

    @property
    def requirements(self):
        for d in dir(self):
            r = getattr(self, d, None)
            if isinstance(r, CommonRequirementWrapper):
                yield r


    def validate_requirements(self):
        result = True
        for r in self.requirements:
            print('%s : %s : %s' % (r.name, r, r.ok))
            if not r.ok:
                result = False
        return result


class Folder(ConfigObject):
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
    def mailpath(self):
        return self.account.mailpath / self.name

    def __str__(self):
        return 'folder %s:%s' % (self.account.name, self.name)

class Account(ConfigObject):

    config_path = PathRequirement('config path')
    procmailrc = FileRequirement('procmail configuration')
    mailcheckrc = FileRequirement('mailcheck configuration')
    mailpath = PathRequirement('mailbox path')

    def __init__(self, name):
        self.name = name
        self.folders = {}

        self.config_path = uttumrc.accounts_path / self.name
        self.procmailrc = self.config_path / 'procmailrc'
        self.mailcheckrc = self.config_path / 'mailcheckrc'
        self.mailpath = uttumrc.mail_path / self.name


    def folder(self, name, **kwargs):
        f = Folder(name)
        for k, v in kwargs.items():
            setattr(f, k, v)
        f.account = self

        self.folders.update({name: f})


    def __str__(self):
        return 'account %s' % self.name

        # return 'account: %s [%s]' % (self.name, ', '.join([f.name for f in self.folders]))


UTTUMRC_TEMPLATE = """
# rename this account
provider = uttumrc.account('provider')
# uncomment this to disable filtering for this account
# provider.procmailrc = None

# uncomment this to disable procmail (filtering) at all
# uttumrc.procmail = None

# define a folder named 'stuff'
provider.folder('stuff', color='#FF0000')
provider.folder('long-project-name', shortcut='project')
provider.folder('not-interesting', notify=False)
"""


class Config(ConfigObject):

    procmail = ProgramRequirement('procmail')
    offlineimap = ProgramRequirement('offlineimap')
    mailcheck = ProgramRequirement('mailcheck')
    twmnc = ProgramRequirement('twmnc')
    msmtp = ProgramRequirement('msmtp')
    uttum = ProgramRequirement('uttum')

    uttumrc_path = FileRequirement('uttumrc path', template=UTTUMRC_TEMPLATE)
    config_path = PathRequirement('configuration path')
    muttrc_path = FileRequirement('muttrc snippet file')
    queue_path = PathRequirement('messages queue path')
    mail_path = PathRequirement('mail path')
    merged_path = PathRequirement('merged mailbox path')
    accounts_path = PathRequirement('accounts path')

    def __init__(self):

        self.config_path = '~/.uttum'
        self.uttumrc_path = self.config_path / 'uttumrc'
        self.muttrc_path = self.config_path / 'muttrc'
        self.accounts_path = self.config_path / 'accounts'

        self.queue_path = self.config_path / 'queue'
        self.mail_path = '~/.mail'
        self.merged_path = self.mail_path / 'merged'

        self.accounts = {}
        self.freeze_time = 10


    def account(self, name):
        _account = Account(name)
        self.accounts.update({name: _account})
        return _account

    @property
    def requirements(self):
        for r in ConfigObject.requirements.__get__(self):
            yield r
        for a in self.accounts.values():
            for r in a.requirements:
                yield r


uttumrc = Config()

def load_config():

    uttumrc.uttumrc_path.try_resolve_if_needed()

    globs = {'uttumrc': uttumrc}
    from six import exec_
    with open(str(uttumrc.uttumrc_path), 'r') as f:
        exec_(f.read(), globs)

load_config()


def show():

    for a in uttumrc.accounts.values():
        print('* account: %s' % a.name)
        for f in a.folders.values():
            print('    * folder: %s' % f.name)
            for k, v in f.__dict__.items():
                if k not in Folder.IGNORE:
                    print('        * %s: %s' % (k, v))

def generate():

    for r in uttumrc.requirements:
        if r.enabled:
            if r.ok:
                print('-- requirement %s is satisfied (%s)' % (r.name, r.value))
            else:
                description = r.try_resolve()
                if r.ok:
                    print('AA requirement %s has been resolved (%s): %s' % (r.name, r.value, description))
                else:
                    print('EE requirement %s failed to be satisfied (%s): %s' % (r.name, r.value_silent, description))

        else:
            print('-- %s is disabled' % r.name)



    for p in uttumrc.merged_path:
        f = uttumrc.merged_path / p
        if not path.islink(f):
            raise Exception('file %s is not link' % f)
        os.remove(f)

    with utils.write_file(uttumrc.muttrc_path.value_silent) as muttrc:
        muttrc.write('# THIS FILE WAS AUTOGENERATED WITH uttum --generate\n')
        muttrc.write('# add following line to your file:\n')
        muttrc.write('# source %s\n' % uttumrc.muttrc_path)
        muttrc.write('set sendmail="/home/psniegowski/bin/uttum --queue --"\n')

        for a in uttumrc.accounts.values():
            with utils.write_file(a.mailcheckrc.value_silent) as mailcheck_file:
                for f in a.folders.values():
                    shortcut = f.real_shortcut
                    link_name = uttumrc.merged_path / shortcut
                    source = f.mailpath

                    muttrc.write('mailboxes +%s\n' % shortcut)
                    mailcheck_file.write('%s\n' % f.mailpath)

                    print('-- creating shortcut: %s -> %s' % (link_name, source))
                    os.symlink(source, link_name)


