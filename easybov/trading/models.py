from easybov.common.models import ModelWithCode, ValidateBaseModel as BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Union
from easybov.trading.enums import (
    OrderStatus,
    OrderType,
    TimeInForce,
    OrderSide,
    TradeEvent,
)


class OrderResponseEntry(BaseModel):
    cl_ord_id: str
    orig_cl_ord_id: Optional[str] = None
    order_id: str
    s_code: str
    s_msg: str


class OrderResponse(ModelWithCode):    
    data: List[OrderResponseEntry]

  
class OrderEntry(BaseModel):
    type: str
    cl_ord_id: str
    orig_cl_ord_id: Optional[str] = None
    order_id: str
    symbol: str
    side: OrderSide
    ord_type: OrderType
    tif: TimeInForce
    order_qty: str
    price: Optional[str] = None
    ord_status: OrderStatus        
    cum_qty: Optional[str] = None
    avg_px: Optional[str] = None    
     

class TradeUpdate(BaseModel):
    event: Union[TradeEvent, str]
    execution_id: Optional[UUID] = None    
    timestamp: datetime
    position_qty: Optional[float] = None
    price: Optional[float] = None
    qty: Optional[float] = None
