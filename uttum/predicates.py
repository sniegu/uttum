from __future__ import print_function, absolute_import

from . import exceptions
import re

class ActionMount(object):

    def bind_predicate(self, predicate):
        raise NotImplementedError()


class Rule(object):

    def __init__(self, predicate, action):
        self.predicate = predicate
        self.action = action

    def process(self, message):
        context = Context(message)
        if self.predicate.matches(context):
            self.action(message)
            return True
        else:
            return False



class Context(object):

    def __init__(self, message):
        self.message = message


class Predicate(object):

    def __call__(self, message):
        return self.matches(Context(message))

    def matches(self, context):
        raise NotImplementedError()

    def __ge__(self, other):
        if isinstance(other, ActionMount):
            other.bind_predicate(self)
        else:
            raise exceptions.ConfigurationException()

    def __and__(self, other):
        return ConjunctionPredicate(self, other)

    def __or__(self, other):
        return AlternativePredicate(self, other)


class TruePredicate(Predicate):

    def matches(self, context):
        return True

    def __str__(self):
        return 'true'


class FalsePredicate(Predicate):

    def matches(self, context):
        return False

    def __str__(self):
        return 'false'


class CompoundPredicate(Predicate):

    def __init__(self, *predicates):
        self.predicates = tuple(predicates)


class AlternativePredicate(CompoundPredicate):

    def matches(self, context):
        for p in self.predicates:
            if p.matches(context):
                return True
        else:
            return False

    def __str__(self):
        return '(' + ' or '.join(map(str, self.predicates)) + ')'


class ConjunctionPredicate(CompoundPredicate):

    def matches(self, context):
        for p in self.predicates:
            if not p.matches(context):
                return False
        else:
            return True

    def __str__(self):
        return '(' + ' and '.join(map(str, self.predicates)) + ')'


class HeaderRegexPredicate(Predicate):

    def __init__(self, header, regex, match=False):
        self.header = header
        self.regex = regex
        self.match = match
        self.compiled = re.compile(regex)

    def matches(self, context):
        header = context.message.get_header(self.header)
        if self.match:
            return self.compiled.match(header) is not None
        else:
            return self.compiled.search(header) is not None

    def __str__(self):
        return '%s ~ "%s"' % (self.header, self.regex)


def parse_predicate(name, value):
    if '_' in name:
        header, operator = name.split('_')
    else:
        header, operator = name, 'equals'

    if operator == 'matches':
        return HeaderRegexPredicate(header, value, match=True)

    if operator == 'contains':
        return HeaderRegexPredicate(header, value, match=False)

    raise exceptions.ConfigurationException()

def construct(*args, **kwargs):

    predicates = list(args)

    for k, v in kwargs.items():
        predicates.append(parse_predicate(k, v))

    if len(predicates) == 0:
        raise exceptions.ConfigurationException()
    return predicates[0] if len(predicates) == 1 else ConjunctionPredicate(*predicates)

Q = construct
true = TruePredicate()
false = FalsePredicate()

