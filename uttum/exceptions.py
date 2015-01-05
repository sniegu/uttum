
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

class CliException(UttumException):
    pass
