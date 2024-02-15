from datetime import datetime
from typing import List

from easybov.common.models import ValidateBaseModel as BaseModel
from pydantic import ConfigDict, Field


class OrderbookLevel(BaseModel):

    price: float = Field(alias="p")
    size: float = Field(alias="s")

    model_config = ConfigDict(protected_namespaces=tuple())


class Orderbook(BaseModel):
    symbol: str
    ts: datetime
    bids: List[OrderbookLevel]
    asks: List[OrderbookLevel]

    model_config = ConfigDict(protected_namespaces=tuple())

    def __init__(self, symbol: str, raw_data):
        processed_data = {
            "symbol": symbol,
            "ts": datetime.fromtimestamp(float(raw_data["data"][0]["ts"])),
            "bids": [OrderbookLevel(p=bid[0], s=bid[1]) for bid in raw_data["data"][0]["bids"]],
            "asks": [OrderbookLevel(p=ask[0], s=ask[1]) for ask in raw_data["data"][0]["asks"]]
        }
        super().__init__(**processed_data)
