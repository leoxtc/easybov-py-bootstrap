from easybov.trading.client import TradingClient
from easybov.trading.requests import GetOrdersRequest

trading_client = TradingClient("B1r6B8EDEe6or5YAAvUP1A",
                               "00b7b5ecd4f2cfba0515ca3167fb9d68d0d8c38ae3df074e04704c1b1ef52c97")

request_params = GetOrdersRequest(cl_ord_id="b11")

order_entry = trading_client.get_order(orderRequest=request_params)

print(order_entry.model_dump_json(exclude_none=True))
