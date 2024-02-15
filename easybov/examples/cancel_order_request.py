from easybov.trading.client import TradingClient
from easybov.trading.requests import CancelOrderRequest
from easybov.trading.enums import OrderSide

trading_client = TradingClient("B1r6B8EDEe6or5YAAvUP1A",
                               "00b7b5ecd4f2cfba0515ca3167fb9d68d0d8c38ae3df074e04704c1b1ef52c97")

cancel_order_data = CancelOrderRequest(
    cl_ord_id="b16",
    orig_cl_ord_id="b15",
    symbol="PETR4",
    price="35.01",
    order_qty="100.00",
    side=OrderSide.SELL
)

cancel_order_reponse = trading_client.cancel_order(order_data=cancel_order_data)

if cancel_order_reponse.code == "0":
    print("Cancel Request sent successfully")
else:
    print("Failed to submit Cancel Request {}".format(cancel_order_reponse.data[0].s_msg))
