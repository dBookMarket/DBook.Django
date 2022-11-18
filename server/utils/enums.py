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
    READER = 'reader'


class TransactionType(BaseEnum):
    SELL = 'sell'
    PURCHASE = 'purchase'
    PRESENT = 'present'


class CeleryTaskStatus(BaseEnum):
    PENDING = 'pending'
    STARTED = 'started'
    RETRY = 'retry'
    FAILURE = 'failure'
    SUCCESS = 'success'


class IssueStatus(BaseEnum):
    PRE_SALE = 'pre_sale'
    ON_SALE = 'on_sale'
    OFF_SALE = 'off_sale'
    UNSOLD = 'unsold'


class SocialMediaType(BaseEnum):
    TWITTER = 'twitter'
    LINKEDIN = 'linkedin'


class BlockChainType(BaseEnum):
    POLYGON = 'polygon'
    BNB = 'bnb'


class Market(BaseEnum):
    FIRST_CLASS = 1
    SECOND_CLASS = 2
