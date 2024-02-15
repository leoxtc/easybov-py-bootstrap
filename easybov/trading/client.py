from easybov.common import RawData
from easybov.common.rest import RESTClient
from typing import Optional,  Union
from easybov.common.enums import BaseURL

from easybov.trading.requests import (
    OrderRequest,
    GetOrdersRequest
    
)

from easybov.trading.models import (
    OrderResponse,
    OrderEntry
)


class TradingClient(RESTClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        raw_data: bool = False,
        url_override: Optional[str] = None,
    ) -> None:        
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            api_version="v1",
            base_url=url_override
            if url_override
            else BaseURL.TRADING_LIVE,
            raw_data=raw_data,
        )

    def submit_order(self, order_data: OrderRequest) -> Union[OrderResponse, RawData]:        
        data = order_data.to_request_fields()
        response = self.post("/trade/order", data)

        if self._use_raw_data:
            return response

        return OrderResponse(**response)
    
    def cancel_order(self, order_data: OrderRequest) -> Union[OrderResponse, RawData]:        
        data = order_data.to_request_fields()
        response = self.post("/trade/cancel-order", data)

        if self._use_raw_data:
            return response

        return OrderResponse(**response)    

    def get_order( self, orderRequest: GetOrdersRequest) -> Union[OrderEntry, RawData]:
     
        params = orderRequest.to_request_fields()

        response = self.get(f"/trade/order", params)

        if self._use_raw_data:
            return response

        return OrderEntry(**response)