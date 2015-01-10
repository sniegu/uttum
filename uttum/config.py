from __future__ import print_function, absolute_import

from os import path, listdir
import os
from .utils import ProgramRequirement, FileRequirement, PathRequirement, CommonRequirement, CommonRequirementWrapper
from . import utils
from . exceptions import SentryException, DeprecatedException
from contextlib import contextmanager
from . import predicates
import mailbox

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


class Message(object):

    def __init__(self, path, name, message):
        self.path = path
        self.name = name
        self.message = message

    @property
    def filename(self):
        result = path.join(self.path, self.message.get_subdir(), self.name)
        info = self.message.get_info()
        if info:
            result += ':' + info
        return result

    def __repr__(self):
        return 'message("%s")' % self.filename

    def __str__(self):
        return 'message("%s")' % self.message.get('Subject')

    @property
    def is_new(self):
        return self.message.get_subdir() == 'new'


class Folder(ConfigObject, predicates.ActionMount):
    notify = True
    link = True
    color = '#cb4b16'
    shortcut = None
    alias = None
    mapping = None
    # TODO: is the default (spoolfile)

    IGNORE = ('name', 'account')

    def __init__(self, account, name):
        self.account = account
        self.name = name
        self.alias = name
        self.maildir = mailbox.Maildir(self.mailpath, factory=None, create=False)

    @property
    def shortcut(self):
        return '%s_%s' % (self.alias, self.account.name)

    @shortcut.setter
    def shortcut(self, value):
        raise DeprecatedException("folder's shortcut attribute is deprecated, use alias instead")

    @property
    def ignore(self):
        return not (self.link or self.notify)

    @ignore.setter
    def ignore(self, value):
        self.link = not value
        self.notify = not value

    @property
    def mailpath(self):
        return self.account.mailpath / self.name

    def __str__(self):
        return 'folder %s:%s' % (self.account.name, self.name)

    def __repr__(self):
        return 'folder(%s:%s)' % (self.account.name, self.name)

    def bind_predicate(self, predicate):
        self.account.rules.append(predicates.Rule(predicate, self.move))

    def move(self, message):
        print('moving %s to %s' % (message, self))

    def filter(self, *args, **kwargs):
        self.bind_predicate(predicates.construct(*args, **kwargs))
        return self

    @property
    def messages(self):
        for k, v in self.maildir.items():
            yield Message(self.mailpath, k, v)
        # return self.maildir.values()

    @property
    def new_messages(self):
        # return filter(lambda m: m.is_new, self.messages)
        root_path = path.join(self.mailpath, 'new')
        for msg_filename in listdir(root_path):
            msg_path = path.join(root_path, msg_filename)
            if not path.exists(msg_path):
                continue

            with open(msg_path) as f:
                message = mailbox.MaildirMessage(f)

            yield Message(self.mailpath, msg_filename, message)


class DictWrapper(object):

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def __getattr__(self, name):
        return self.dictionary[name]

    def __getitem__(self, name):
        return self.dictionary[name]

    def __iter__(self):
        return iter(self.dictionary.values())

    def __str__(self):
        return str(self.dictionary.values())


class Account(ConfigObject):

    config_path = PathRequirement('config path')
    procmailrc = FileRequirement('procmail configuration')
    mailcheckrc = FileRequirement('mailcheck configuration')
    mailpath = PathRequirement('mailbox path')
    # TODO: default_address

    def __init__(self, name):
        self.name = name
        self._folders = {}
        self.rules = list()

        self.config_path = uttumrc.accounts_path / self.name
        self.procmailrc = self.config_path / 'procmailrc'
        self.mailcheckrc = self.config_path / 'mailcheckrc'
        self.mailpath = uttumrc.mail_path / self.name


    def folder(self, name, **kwargs):
        try:
            f = self._folders[name]
        except KeyError:
            f = Folder(self, name)
            f.account = self
            self._folders[name] = f

        for k, v in kwargs.items():
            setattr(f, k, v)

        return f


    def find_folders(self):

        uttumrc.raise_for_sentry()

        for name in self.mailpath:
            if 'cur' in os.listdir(self.mailpath / name):
                self.folder(name)


    def locked(self, timeout=5):
        return utils.locked_file(uttumrc.mail_path / ('.%s-sync.lock' % self.name), timeout=5)



    def __str__(self):
        return 'account %s' % self.name

    def __repr__(self):
        return 'account(%s)' % self.name

        # return 'account: %s [%s]' % (self.name, ', '.join([f.name for f in self.folders]))

    @property
    def folders(self):
        return DictWrapper(self._folders)


UTTUMRC_TEMPLATE = """
# uttumrc.procmail = None

# rename this account
provider = uttumrc.account('provider')
# auto find all folders
provider.find_folders()

# uncomment this to disable filtering for this account
# provider.procmailrc = None

# uncomment this to disable procmail (filtering) at all

# define attributes on a folder named 'stuff'
# (and add it to configuration, if it is not already configured)
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

    offlineimaprc_path = FileRequirement('offlineimap path')
    uttumrc_path = FileRequirement('uttumrc path', template=UTTUMRC_TEMPLATE)
    config_path = PathRequirement('configuration path')
    muttrc_path = FileRequirement('muttrc snippet file')
    queue_path = PathRequirement('messages queue path')
    mail_path = PathRequirement('mail path')
    merged_path = PathRequirement('merged mailbox path')
    accounts_path = PathRequirement('accounts path')
    sentry_path = PathRequirement('sentry path')

    def __init__(self):

        self.config_path = '~/.uttum'
        self.offlineimaprc_path = '~/.offlineimap'

        self.uttumrc_path = self.config_path / 'uttumrc'
        self.muttrc_path = self.config_path / 'muttrc'
        self.accounts_path = self.config_path / 'accounts'

        self.queue_path = self.config_path / 'queue'
        self.mail_path = '~/.mail'
        self.merged_path = self.mail_path / 'merged'

        self.sentry_path  = self.mail_path / 'sentry'

        self._accounts = {}
        self.freeze_time = 10



    def account(self, name):
        _account = Account(name)
        self._accounts.update({name: _account})
        return _account

    @property
    def accounts(self):
        return DictWrapper(self._accounts)

    @property
    def requirements(self):
        for r in ConfigObject.requirements.__get__(self):
            yield r
        for a in self.accounts:
            for r in a.requirements:
                yield r

    def raise_for_sentry(self):
        if self.sentry_path.invalid:
            raise SentryException()


uttumrc = Config()

def load_config():


    globs = {'uttumrc': uttumrc}
    from six import exec_
    if uttumrc.uttumrc_path:
        with open(uttumrc.uttumrc_path.value, 'r') as f:
            exec_(f.read(), globs)

load_config()


def show():

    for a in uttumrc.accounts:
        print('* account: %s' % a.name)
        for f in a.folders:
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
        muttrc.write('# add following line to your muttrc file:\n')
        muttrc.write('# source %s\n' % uttumrc.muttrc_path)
        muttrc.write('set sendmail="%s --queue --"\n' % uttumrc.uttum.value)

        for a in uttumrc.accounts:
            with utils.write_file(a.mailcheckrc.value_silent) as mailcheck_file:
                for f in a.folders:
                    if not f.link:
                        continue
                    link_name = uttumrc.merged_path / f.shortcut
                    source = f.mailpath

                    muttrc.write('mailboxes +%s\n' % f.shortcut)
                    if f.mapping is not None:
                        muttrc.write('macro index %s "<change-folder>\cu=%s<enter>" "change folder to %s %s"\n' % (f.mapping, f.shortcut, f.account.name, f.name))

                    mailcheck_file.write('%s\n' % f.mailpath)

                    print('-- creating shortcut: %s -> %s' % (link_name, source))
                    os.symlink(source, link_name)


