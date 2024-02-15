from easybov.data.live.b3 import B3DataStream


#wss_client = B3DataStream('api-key', 'secret-key')

orders_data_stream = B3DataStream("B1r6B8EDEe6or5YAAvUP1A",
                                   "00b7b5ecd4f2cfba0515ca3167fb9d68d0d8c38ae3df074e04704c1b1ef52c97")


async def order_data_handler(data):
    # json com as atualizações de ordens, como: nova ordem, cancelamento, execucao, etc
    print(data)

orders_data_stream.subscribe_orders(order_data_handler)

orders_data_stream.run()