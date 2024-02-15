import asyncio
import logging
import queue
import hashlib
import hmac
import json
import time
from collections import defaultdict
from typing import Callable, Dict, Optional, Union, Tuple
import websockets
from pydantic import BaseModel
from easybov import __version__

from easybov.common.types import RawData
from easybov.data.models.order_book import Orderbook
from easybov.data.models.order_update import OrderUpdate

log = logging.getLogger(__name__)


class BaseStream:
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        websocket_params: Optional[Dict] = None,
    ) -> None:        
        self._endpoint = endpoint
        self._api_key = api_key
        self._secret_key = secret_key
        self._ws = None
        self._running = False
        self._loop = None
        self._raw_data = raw_data
        self._stop_stream_queue = queue.Queue()
        self._handlers = {
            "books": {},
            "orders": {},            
        }
        self._name = "data"
        self._should_run = True
        self._max_frame_size = 32768

        self._websocket_params = {
            "ping_interval": 10,
            "ping_timeout": 180,
            "max_queue": 1024,
        }

        if websocket_params:
            self._websocket_params = websocket_params

    async def _connect(self) -> None:
        extra_headers = {
            "Content-Type": "application/json",
            "User-Agent": "EASYBOV-PY/" + __version__,
        }

        self._ws = await websockets.connect(
            self._endpoint,
            extra_headers=extra_headers,
            **self._websocket_params,
        )

    def _generate_signature(self, timestamp: float) -> str:
        hash_module = hashlib.sha512()
        hash_module.update("".encode('utf-8'))
        hashed_payload = hash_module.hexdigest()
        s = '%s\n%s\n%s\n%s\n%s' % ("GET", "/api/v1/users/verify", "", hashed_payload, timestamp)
        return hmac.new(self._secret_key.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()

    def _ws_login_request(self) -> str:
        ts = time.time()
        sign = self._generate_signature(ts)

        login_dict = {"op": "login", "args": [{"api_key": self._api_key, "timestamp": str(ts), "sign": sign}]}
        return json.dumps(login_dict)

    async def _auth(self) -> None:        
        await self._ws.send(
            self._ws_login_request()           
        )

        r = await self._ws.recv()

        msg = json.loads(r)
        
        if msg["code"] != '0':
            raise ValueError("auth failed {} {}".format(msg["code"], msg["msg"]))        

    async def _start_ws(self) -> None:        
        await self._connect()
        await self._auth()
        log.info(f"connected to: {self._endpoint}")

    async def close(self) -> None:        
        if self._ws:
            await self._ws.close()
            self._ws = None
            self._running = False

    async def stop_ws(self) -> None:        
        self._should_run = False
        if self._stop_stream_queue.empty():
            self._stop_stream_queue.put_nowait({"should_stop": True})

    async def _consume(self) -> None:        
        while True:
            if not self._stop_stream_queue.empty():
                self._stop_stream_queue.get(timeout=1)
                await self.close()
                break
            else:
                try:
                    msg = await asyncio.wait_for(self._ws.recv(), 5)                                        
                    await self._dispatch(json.loads(msg))
                except asyncio.TimeoutError:
                    # ws.recv is hanging when no data is received. by using
                    # wait_for we break when no data is received, allowing us
                    # to break the loop when needed
                    pass

    def _cast(self, msg_type: str, msg: Dict) -> Union[BaseModel, RawData]:
        result = msg
        if not self._raw_data:
            if msg_type == "books":
                result = Orderbook(msg["arg"]["symbol"], msg)
            elif msg_type == "orders":
                result = OrderUpdate(msg["arg"]["symbol"], msg)

        return result

    async def _dispatch(self, msg: Dict) -> None:
        msg_type = msg["event"] if "event" in msg.keys() else msg["arg"]["channel"]
        symbol = msg["arg"]["symbol"]
        #if msg_type == "trades":
            #handler = self._handlers["trades"].get(
            #    symbol, self._handlers["trades"].get("*", None)
            #)
            #if handler:
             #   await handler(self._cast(msg_type, msg))
        if msg_type == "books":
            handler = self._handlers["books"].get(
                symbol, self._handlers["books"].get("*", None)
            )
            if handler:
                await handler(self._cast(msg_type, msg))
        elif msg_type == "orders":
            handler = self._handlers["orders"].get(
                symbol, self._handlers["orders"].get("*", None)
            )
            if handler:
                await handler(self._cast(msg_type, msg))
        elif msg_type == "subscribe":
            log.info("subscribed to {}:{}".format(msg["arg"]["channel"], msg["arg"]["symbol"]))
        elif msg_type == "error":
            log.error(f'error: {msg.get("msg")} ({msg.get("code")})')

    def _subscribe(
        self, handler: Callable, symbols: Tuple[str], handlers: Dict
    ) -> None:
        self._ensure_coroutine(handler)
        for symbol in symbols:
            handlers[symbol] = handler
        if self._running:
            asyncio.run_coroutine_threadsafe(self._subscribe_all(), self._loop).result()

    async def _subscribe_all(self) -> None:
        msg = defaultdict(list)
        channel_list = []
        for k, v in self._handlers.items():
            if k not in ("cancelErrors", "corrections") and v:
                for s in v.keys():
                    channel_list.append({"channel": k, "symbol": s})

        msg["op"] = "subscribe"
        msg["args"] = channel_list
        await self._ws.send(json.dumps(msg))

    async def _unsubscribe(self, trades=(), books=(), orders=()) -> None:
        if trades or books or orders:
            await self._ws.send(
                    json.dumps({
                        "action": "unsubscribe",
                        "trades": trades,
                    })
            )

    async def _run_forever(self) -> None:
        self._loop = asyncio.get_running_loop()
        # do not start the websocket connection until we subscribe to something
        while not any(
            v
            for k, v in self._handlers.items()
            if k not in ("cancelErrors", "corrections")
        ):
            if not self._stop_stream_queue.empty():
                # the ws was signaled to stop before starting the loop so
                # we break
                self._stop_stream_queue.get(timeout=1)
                return
            await asyncio.sleep(0)
        log.info(f"started {self._name} stream")
        self._should_run = True
        self._running = False
        while True:
            try:
                if not self._should_run:
                    # when signaling to stop, this is how we break run_forever
                    log.info("{} stream stopped".format(self._name))
                    return
                if not self._running:
                    log.info("starting {} websocket connection".format(self._name))
                    await self._start_ws()
                    await self._subscribe_all()
                    self._running = True
                await self._consume()
            except websockets.WebSocketException as wse:
                await self.close()
                self._running = False
                log.warning("data websocket error, restarting connection: " + str(wse))
            except Exception as e:
                log.exception(
                    "error during websocket " "communication: {}".format(str(e))
                )
            finally:
                await asyncio.sleep(0)

    def subscribe_trades(self, handler: Callable, *symbols) -> None:
        self._subscribe(handler, symbols, self._handlers["trades"])

    def subscribe_books(self, handler: Callable, *symbols) -> None:
        self._subscribe(handler, symbols, self._handlers["books"])

    def subscribe_orders(self, handler: Callable) -> None:
        self._subscribe(handler, "*", self._handlers["orders"])

    def unsubscribe_trades(self, *symbols) -> None:        
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._unsubscribe(trades=symbols), self._loop
            ).result()
        for symbol in symbols:
            del self._handlers["trades"][symbol]

    def unsubscribe_books(self, *symbols) -> None:
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._unsubscribe(books=symbols), self._loop
            ).result()
        for symbol in symbols:
            del self._handlers["books"][symbol]

    def unsubscribe_orders(self) -> None:
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._unsubscribe(orders="*"), self._loop
            ).result()
        del self._handlers["orders"]["*"]

    def run(self) -> None:
        try:
            asyncio.run(self._run_forever())
        except KeyboardInterrupt:
            print("keyboard interrupt, bye")
            pass
        finally:
            self.stop()

    def stop(self) -> None:        
        if self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.stop_ws(), self._loop).result()

    @staticmethod
    def _ensure_coroutine(handler: Callable) -> None:
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError("handler must be a coroutine function")
