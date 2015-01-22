from __future__ import print_function, absolute_import

from . import exceptions
import re
import functools

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

def false_on_missing_header(func):

    @functools.wraps
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions.MissingHeaderException as e:
            return False

    return wrapped

class HeaderRegexPredicate(Predicate):

    def __init__(self, header, regex):
        self.header = header
        self.regex = regex
        self.compiled = re.compile(regex)

    @false_on_missing_header
    def matches(self, context):
        return self.compiled.search(context.message.get_header(self.header)) is not None

    def __str__(self):
        return '(%s ~ "%s")' % (self.header, self.regex)

class ContactHeaderPredicate(Predicate):

    def __init__(self, header, contact):
        self.header = header
        self.contact = contact

    @false_on_missing_header
    def matches(self, context):
        return self.contact in context.message.get_header(self.header)

    def __str__(self):
        return '("%s" in %s)' % (self.contact, self.header)


def parse_predicate(name, value):
    if '_' in name:
        header, operator = name.split('_')
    else:
        header, operator = name, None

    if operator is None:
        if header == 'contacts':
            contact = value
            return AlternativePredicate(ContactHeaderPredicate('to', contact), ContactHeaderPredicate('from', contact), ContactHeaderPredicate('cc', contact))

    if operator == 'matches':
        return HeaderRegexPredicate(header, value)


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

