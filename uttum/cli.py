#!/usr/bin/env python
# if sys.version_info.major < 3:
from __future__ import print_function, absolute_import


from uttum import utils
from uttum.messages import Message
from uttum import sending, syncing, config, filtering, checking
import signal
import argparse
import sys


def noop_handler(signum, frame):
    print('received signal')


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
    parser.add_argument('--unlocked', dest='unlocked', action='store_true', help='')
    parser.add_argument('-f', '--filter', dest='filter', action='store_true', help='')
    parser.add_argument('--folder', dest='folder', action='store', default='INBOX')
    parser.add_argument('-c', '--current', dest='category', action='store_const', const='cur', default='new')
    parser.add_argument('--notify', dest='notifies', action='append', default=[])

    parser.add_argument('--queue', dest='queue', action='store_true')
    parser.add_argument('--check-all', dest='check_all', action='store_true')
    parser.add_argument('--generate', dest='generate', action='store_true')


    with utils.signal_handler(signal.SIGUSR1, noop_handler):
        argv = list(sys.argv[1:])

        try:
            i = argv.index('--')
            args = argv[0:i]
            other = argv[i + 1:]
        except ValueError:
            args, other = argv, []

        args = parser.parse_args(args)

        if len(args.accounts) == 0:
            accounts = config.config.accounts.values()
        else:
            accounts = [config.config.accounts[a] for a in args.accounts]

        if len(args.messages) == 0:
            messages = list(Message.list_all())
        else:
            messages = [Message(m) for m in args.messages]



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
            for m in messages:
                sending.status(m)

        if args.send:
            for m in messages:
                if not sending.send(m):
                    sys.exit(1)

        if args.freeze:
            for m in messages:
                sending.freeze(m)


        if args.check:
            syncing.check()

        if args.check_bg:
            syncing.check_bg()

        if args.sync:
            for a in accounts:
                (syncing.unlocked_sync if args.unlocked else syncing.sync)(a)

        if args.filter:
            for a in accounts:
                filtering.filter(a, folder=args.folder, kind=args.category)

        for n in args.notifies:
            utils.notify(n)


