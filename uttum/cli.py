#!/usr/bin/env python
# if sys.version_info.major < 3:
from __future__ import print_function, absolute_import


from uttum import commands
from uttum import utils
from uttum.config import config
from uttum.messages import Message
import signal
import argparse


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
        (args, unknown_args) = parser.parse_known_args()

        if len(args.accounts) == 0:
            accounts = config.accounts.values()
        else:
            accounts = [config.accounts[a] for a in args.accounts]

        if len(args.messages) == 0:
            messages = list(Message.list_all())
        else:
            messages = [Message(m) for m in args.messages]

        if args.queue:
            commands.queue(unknown_args)

        if args.generate:
            commands.generate()

        if args.check_all:
            commands.check_all()

        if args.check:
            commands.check()

        if args.check_bg:
            commands.check_bg()

        if args.show:
            commands.show()

        if args.abort:
            commands.abort()

        if args.status:
            for m in messages:
                commands.status(m)

        if args.send:
            for m in messages:
                commands.send(m)

        if args.freeze:
            for m in messages:
                commands.freeze(m)

        if args.sync:
            for a in accounts:
                (commands.unlocked_sync if args.unlocked else commands.sync)(a)

        if args.filter:
            for a in accounts:
                commands.filter(a, folder=args.folder, kind=args.category)

        for n in args.notifies:
            commands.notify(n)


