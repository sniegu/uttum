
class UttumException(Exception):
    pass

class RequirementNotSatisfied(UttumException):
    pass

class SentryException(UttumException):
    pass
