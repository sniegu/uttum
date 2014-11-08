#!/usr/bin/env python
# if sys.version_info.major < 3:
from __future__ import print_function, absolute_import


from uttum.parser import parser
from uttum import commands
from uttum import utils
import signal


def noop_handler(signum, frame):
    print('received signal')

if __name__ == '__main__':
    with utils.signal_handler(signal.SIGUSR1, noop_handler):
        parser.parse()

