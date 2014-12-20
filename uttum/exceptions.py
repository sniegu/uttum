
class UttumException(Exception):
    pass

class DeprecatedException(UttumException):
    pass

class RequirementNotSatisfied(UttumException):
    pass

class SentryException(UttumException):
    pass

class LockException(UttumException):
    pass
