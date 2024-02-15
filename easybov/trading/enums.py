from enum import Enum


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderSide(str, Enum):
    BUY = "1"
    SELL = "2"


class OrderStatus(str, Enum):
    NEW = "0"
    PARTIALLY_FILLED = "1"
    FILLED = "2"
    DONE_FOR_DAY = "3"
    CANCELED = "4"
    REPLACED = "5"
    PENDING_CANCEL = "6"
    STOPPED = "7"
    REJECTED = "8"
    SUSPENDED = "9"
    PENDING_NEW = "A"
    CALCULATED = "B"
    EXPIRED = "C"
    PENDING_REPLACE = "E"





class TimeInForce(str, Enum):
    DAY = "0"
    GTC = "1"
    IOC = "3"
    FOK = "4"


class TradeEvent(str, Enum):
    FILL = "fill"
    CANCELED = "canceled"
    NEW = "new"
    PARTIAL_FILL = "partial_fill"