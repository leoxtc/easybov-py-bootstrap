from datetime import datetime
from typing import Optional, Any
from pydantic import model_validator

from easybov.common.models import ModelWithID
from easybov.common.requests import NonEmptyRequest
from easybov.trading.enums import (
    OrderType,
    TimeInForce,
    OrderSide
)


class CancelOrderResponse(ModelWithID):
    status: int


class OrderRequest(NonEmptyRequest):
    symbol: str
    cl_ord_id: str
    order_qty: str = None    
    side: OrderSide    
    ord_type: Optional[OrderType] = None
    tif: Optional[TimeInForce] = None    

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        order_qty = "order_qty" in values and values["order_qty"] is not None
      
        if not order_qty:
            raise ValueError("order qty must be provided")        

        return values


class MarketOrderRequest(OrderRequest):
    def __init__(self, **data: Any) -> None:        

        data["ord_type"] = OrderType.MARKET

        super().__init__(**data)


class LimitOrderRequest(OrderRequest):
    price: str

    def __init__(self, **data: Any) -> None:
        
        data["ord_type"] = OrderType.LIMIT

        super().__init__(**data)


class CancelOrderRequest(OrderRequest):
    orig_cl_ord_id: str

    def __init__(self, **data: Any) -> None:

        super().__init__(**data)

class GetOrdersRequest(NonEmptyRequest):
    cl_ord_id: str
    symbol: Optional[str] = None
    after: Optional[datetime] = None
    until: Optional[datetime] = None
    