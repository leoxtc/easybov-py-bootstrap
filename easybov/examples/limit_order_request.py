from easybov.trading.client import TradingClient
from easybov.trading.requests import LimitOrderRequest
from easybov.trading.enums import OrderSide, TimeInForce

trading_client = TradingClient("B1r6B8EDEe6or5YAAvUP1A",
                               "00b7b5ecd4f2cfba0515ca3167fb9d68d0d8c38ae3df074e04704c1b1ef52c97")

limit_order_data = LimitOrderRequest(
    cl_ord_id="b12",
    symbol="PETR4",
    price="45300.01",
    order_qty="100.00",
    side=OrderSide.BUY,
    tif=TimeInForce.DAY
)

limit_order_reponse = trading_client.submit_order(order_data=limit_order_data)

if limit_order_reponse.code == "0":
    print("Order has been placed successfully")
