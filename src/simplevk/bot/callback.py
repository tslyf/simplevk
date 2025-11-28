import logging
import time
import typing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import orjson

from simplevk.bot.api import RobustLongPoll

if typing.TYPE_CHECKING:
    from simplevk.bot import Bot

logger = logging.getLogger("simplevk")


def _handler_factory(
    bot_instance: "Bot",
    secret_key: str,
    path: str,
    confirmation_code: str,
    started_time: float,
):
    class CallbackHandler(BaseHTTPRequestHandler):
        _bot = bot_instance
        _secret = secret_key
        _path = path
        _confirm_code = confirmation_code
        _server_start_time = started_time

        def do_POST(self):
            if self.path != self._path:
                self.send_error(404, "Not Found")
                return

            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len)
                data = orjson.loads(body)
            except Exception as e:
                logger.warning(f"Callback: Invalid request data: {e}")
                self.send_error(400, "Bad Request")
                return

            if data.get("secret") != self._secret:
                logger.warning("Callback: Invalid secret key")
                self.send_error(403, "Forbidden")
                return

            event_type = data.get("type")

            if event_type == "confirmation":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(self._confirm_code.encode())
                logger.info("Callback: Confirmation code sent successfully.")
                return

            try:
                event = RobustLongPoll._cls_parse_event(data)
                event_date = 0
                if event.message:
                    event_date = event.message.get("date", 0)
                elif event.obj:
                    event_date = event.obj.get("date", 0)

                if event_date != 0 and event_date < self._server_start_time:
                    logger.debug(
                        f"Callback: Ignored old event (ID: {data.get('event_id')})"
                    )
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"ok")
                    return

                self._bot.executor.submit(self._bot.handle_events, event, "cb")

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            except Exception:
                logger.exception("Callback: Error handling event")
                self.send_error(500, "Internal Server Error")
                return

        def log_message(self, format, *args):
            logger.debug(f"Callback request: {self.address_string()} - {format % args}")

    return CallbackHandler


class CallbackServer:
    def __init__(self, bot: "Bot", host: str, port: int, path: str, secret_key: str):
        self.bot = bot
        self.host = host
        self.port = port
        self.path = path
        self.secret_key = secret_key

        self.httpd: ThreadingHTTPServer | None = None
        self.thread: Thread | None = None
        self.started_time = 0

        self._confirmation_code: str | None = None

    def _fetch_confirmation_code(self) -> str:
        try:
            logger.info("Callback: Fetching confirmation code...")
            confirmation_code = self.bot.api.groups.getCallbackConfirmationCode(
                group_id=self.bot.group_id
            )["code"]
            logger.info("Callback: Confirmation code received.")
            return confirmation_code
        except Exception as e:
            logger.critical("Callback: Failed to get confirmation code", exc_info=True)
            raise RuntimeError("Failed to get confirmation code from VK API.") from e

    def start(self):
        logger.info(
            f"Callback server starting on http://{self.host}:{self.port}{self.path}"
        )
        if self._confirmation_code is None:
            self._confirmation_code = self._fetch_confirmation_code()

        HandlerClass = _handler_factory(
            self.bot,
            self.secret_key,
            self.path,
            self._confirmation_code,
            self.started_time,
        )

        self.httpd = ThreadingHTTPServer((self.host, self.port), HandlerClass)
        self.started_time = self.bot.longpoll.ts or time.time()

        self.thread = Thread(
            target=self.httpd.serve_forever,
            name=f"CallbackServerThread_G{self.bot.group_id}",
        )
        self.thread.daemon = True
        self.thread.start()
        logger.info("Callback server started")

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        logger.info("Callback server stopped")
