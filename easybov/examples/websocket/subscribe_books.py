from easybov.data.live.b3 import B3DataStream

market_data_stream = B3DataStream("B1r6B8EDEe6or5YAAvUP1A",
                                   "00b7b5ecd4f2cfba0515ca3167fb9d68d0d8c38ae3df074e04704c1b1ef52c97")


async def book_data_handler(data):
    print(data)

market_data_stream.subscribe_books(book_data_handler, "PETR4")

market_data_stream.run()
