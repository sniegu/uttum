from __future__ import print_function, absolute_import
from . import exceptions

class ActionMount(object):

    def bind_predicate(self, predicate):
        raise NotImplementedError()


class Rule(object):

    def __init__(self, predicate, action):
        self.predicate = predicate
        self.action = action

    def process(self, message):
        if self.predicate(message):
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

true = TruePredicate()
false = FalsePredicate()

