from typing import Optional, Dict

from easybov.common.enums import BaseURL
from easybov.common.websocket import BaseStream


class B3DataStream(BaseStream):
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,        
        websocket_params: Optional[Dict] = None,
        url_override: Optional[str] = None,
    ) -> None:                
        super().__init__(
            endpoint=(
                url_override
                if url_override is not None
                else BaseURL.WS_DATA_STREAM.value + "/v1"
            ),
            api_key=api_key,
            secret_key=secret_key,
            raw_data=raw_data,
            websocket_params=websocket_params,
        )
