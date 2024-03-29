from enum import Enum


class BaseURL(str, Enum):    
    TRADING_LIVE = "https://easybov.com"
    #TRADING_LIVE = "http://localhost:8001"
    WS_DATA_STREAM = "wss://easybov.com/ws"
    #WS_DATA_STREAM = "ws://localhost:9003"


class PaginationType(str, Enum):
    """
    An enum for choosing what type of pagination of results you'd like for BrokerClient functions that support
    pagination.

    Attributes:
        NONE: Requests that we perform no pagination of results and just return the single response the API gave us.
        FULL: Requests that we perform all the pagination and return just a single List/dict/etc containing all the
          results. This is the default for most functions.
        ITERATOR: Requests that we return an Iterator that yields one "page" of results at a time
    """

    NONE = "none"
    FULL = "full"
    ITERATOR = "iterator"


class Sort(str, Enum):
    ASC = "asc"
    DESC = "desc"