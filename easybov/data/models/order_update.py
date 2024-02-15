from easybov.trading.enums import OrderSide, OrderStatus
from easybov.common.models import ValidateBaseModel as BaseModel
from typing import Optional
from pydantic import ConfigDict


class OrderUpdate(BaseModel):
    symbol: str
    cl_ord_id: str
    orig_cl_ord_id: Optional[str] = None
    side: OrderSide
    price: float
    last_px: float
    last_qty: float
    cum_qty: float
    order_qty: float
    ord_type: str
    ord_status: OrderStatus
    transact_time: str

    model_config = ConfigDict(protected_namespaces=tuple())

    def __init__(self, symbol: str, raw_data):
        super().__init__(**raw_data["data"][0])
