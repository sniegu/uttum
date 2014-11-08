from __future__ import print_function, absolute_import

from uttum.config import config, debug
import argparse
import inspect
import sys

def generate_help(parser):
    def help():
        parser.parser.print_help()
    return help



class Parser(object):

    def __init__(self, name):
        self.parser = argparse.ArgumentParser(description=name)
        self.subparsers = self.parser.add_subparsers(title='command')
        # self.classic = self.subparsers.add_parser('classic')
        # self.classic.set_defaults(func=self.classic_call)
        # self.add(generate_help(self))


    def simple_command(self, function):
        subparser = self.subparsers.add_parser(function.__name__)

        def wrapper(args):

            result = function()
            if result is not None:
                print(result)

        subparser.set_defaults(func=wrapper)

        return function


    def add(self, function):

        args_names, varargs, keywords, defaults = inspect.getargspec(function)

        first_default = len(args_names) - (len(defaults) if defaults else 0)
        subparser = self.subparsers.add_parser(function.__name__)
        for i in range(0, len(args_names)):
            default = (defaults[i - first_default] if i >= first_default else None)
            name = args_names[i]
            arg = dict()
            # print('default: %s=%s' % (name , default))
            if default:
                arg.update(nargs='?', default=default)
            elif name[-1] == 's':
                arg.update(nargs='+')

            subparser.add_argument(name, **arg)

        def wrapper(args):
            v = vars(args)
            values = {k:v[k] for k in args_names}
            if 'account' in values:
                values['account'] = config.accounts[values['account']]

            # print(values)
            result = function(**values)
            if result is not None:
                print(result)

        subparser.set_defaults(func=wrapper)

        return function

    def parse(self):
        (self.known_args, self.unknown_args) = self.parser.parse_known_args(['help'] if len(sys.argv) == 1 else sys.argv[1:])
        self.known_args.func(self.known_args)

parser = Parser('uttum')
