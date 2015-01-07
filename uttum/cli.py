#!/usr/bin/env python
# if sys.version_info.major < 3:
from __future__ import print_function, absolute_import


from uttum import utils
import signal
import argparse
import sys
from uttum.exceptions import UttumException
from contextlib import contextmanager


def noop_handler(signum, frame):
    print('received signal')

@contextmanager
def dummy_context_manager():
    yield

def process(args):

    def accounts(default_all=True):
        from uttum.config import uttumrc
        if len(args.accounts) == 0:
            if default_all:
                return uttumrc.accounts.values()
            else:
                raise CliException('must explicitely specify at least one account')
        else:
            return [uttumrc.accounts[a] for a in args.accounts]

    def messages():

        from uttum.messages import Message

        if len(args.messages) == 0:
            return list(Message.list_all())
        else:
            return [Message(m) for m in args.messages]

    def locked(account):
        if args.unlocked:
            return dummy_context_manager()
        else:
            return account.locked()


    from uttum import sending, syncing, config, filtering, checking

    if args.check_all:
        print(checking.check_all())

    if args.show:
        config.show()

    if args.generate:
        config.generate()

    if args.abort:
        sending.abort()

    if args.queue:
        sending.queue(other)

    if args.status:
        for m in messages():
            sending.status(m)

    if args.send:
        for m in messages():
            if not sending.send(m):
                sys.exit(1)

    if args.freeze:
        for m in messages():
            sending.freeze(m)

    if args.check:
        syncing.check()

    if args.check_bg:
        syncing.check_bg()

    if args.sync:
        for account in accounts():
            with locked(account):
                if args.folders:
                    for f in args.folders:
                        syncing.sync_folder(account.folders[f])
                else:
                    syncing.sync(account)

    if args.fetch:
        for account in accounts():
            with locked(account):
                syncing.fetch(account)

    if args.create:
        for account in accounts(default_all=False):
            with locked(account):
                for f in args.folders:
                    syncing.create_folder(account, f)


    if args.filter:
        for account in accounts():
            with locked(account):
                folders = args.folders if args.folders else ['INBOX']
                for f in args.folders:
                    filtering.filter(account, folder=f, kind=args.category)


    for n in args.notifies:
        utils.notify(n)

    if args.reqs:
        from uttum.config import uttumrc
        if not uttumrc.validate_requirements():
            sys.exit(1)

    if args.shell:
        from IPython import embed ; embed()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='uttum')
    parser.add_argument('-a', '--account', dest='accounts', action='append', default=[], help='accounts to operate on, default is all')

    parser.add_argument('--check', dest='check', action='store_true')
    parser.add_argument('--check-bg', dest='check_bg', action='store_true')
    parser.add_argument('--show', dest='show', action='store_true')
    parser.add_argument('--abort', dest='abort', action='store_true')

    parser.add_argument('-m', '--message', dest='messages', action='append', default=[], help='')
    parser.add_argument('--status', dest='status', action='store_true')
    parser.add_argument('-s', '--send', dest='send', action='store_true', help='')
    parser.add_argument('--freeze', dest='freeze', action='store_true', help='')

    parser.add_argument('-y', '--sync', dest='sync', action='store_true', help='')
    parser.add_argument('-e', '--fetch', dest='fetch', action='store_true', default=False, help='')
    parser.add_argument('--unlocked', dest='unlocked', action='store_true', help='')
    parser.add_argument('-f', '--filter', dest='filter', action='store_true', help='')
    parser.add_argument('-d', '--folder', dest='folders', action='append', default=[])
    parser.add_argument('-c', '--current', dest='category', action='store_const', const='cur', default='new')
    parser.add_argument('--notify', dest='notifies', action='append', default=[])
    parser.add_argument('--create', dest='create', action='store_true', default=False)

    parser.add_argument('--queue', dest='queue', action='store_true')
    parser.add_argument('--check-all', dest='check_all', action='store_true')
    parser.add_argument('--generate', dest='generate', action='store_true')

    parser.add_argument('--shell', dest='shell', action='store_true')
    parser.add_argument('--reqs', dest='reqs', action='store_true', help='check requirements')


    with utils.signal_handler(signal.SIGUSR1, noop_handler):
        argv = list(sys.argv[1:])

        try:

            try:
                i = argv.index('--')
                args = argv[0:i]
                other = argv[i + 1:]
            except ValueError:
                args, other = argv, []

            args = parser.parse_args(args)

            process(args)

        except UttumException as e:
            print('%s' % e)
            sys.exit(1)
        except Exception as e:
            # print('error: %s' % e, file=sys.stderr)
            raise
            # sys.exit(1)

