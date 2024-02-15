from typing import Dict

QUOTE_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "ax": "ask_exchange",
    "ap": "ask_price",
    "as": "ask_size",
    "bx": "bid_exchange",
    "bp": "bid_price",
    "bs": "bid_size",
    "c": "conditions",
    "z": "tape",
}

TRADE_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "p": "price",
    "s": "size",
    "x": "exchange",
    "i": "id",
    "c": "conditions",
    "z": "tape",
}

ORDERBOOK_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "b": "bids",
    "a": "asks",
}

ORDERBOOK_QUOTE_MAPPING: Dict[str, str] = {
    "p": "price",
    "s": "size",
}
