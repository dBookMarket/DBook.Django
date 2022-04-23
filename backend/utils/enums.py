from enum import Enum, unique


@unique
class BaseEnum(Enum):
    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in list(cls)]


class UserType(BaseEnum):
    AUTHOR = 'author'
    PUBLISHER = 'publisher'
    NORMAL = 'normal'


class TransactionType(BaseEnum):
    SELL = 'sell'
    PURCHASE = 'purchase'
    PRESENT = 'present'


class CeleryTaskStatus(BaseEnum):
    PENDING = 'PENDING'
    STARTED = 'STARTED'
    RETRY = 'RETRY'
    FAILURE = 'FAILURE'
    SUCCESS = 'SUCCESS'


class IssueStatus(BaseEnum):
    UPLOADING = 'Uploading'
    UPLOADED = 'Uploaded'
    FAILURE = 'Failure'
    SUCCESS = 'Success'
