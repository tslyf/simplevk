import logging
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread
from typing import Any, Callable

import vk_api
from requests import Timeout
from urllib3.exceptions import ReadTimeoutError
from vk_api.bot_longpoll import VkBotEvent, VkBotMessageEvent

from simplevk.events import events
from simplevk.labeler.bot_labeler import BotLabeler
from simplevk.objects.messages import SentMessage
from simplevk.rules import BaseRule
from simplevk.rules import rules as BASE_RULES
from simplevk.utils.functions import LimitedDict

from .api import RobustLongPoll, RobustVkApi
from .callback import CallbackServer


def base_error_handler(error: Exception, event: Any = None):
    logging.getLogger().exception("Error handling event")


logger = logging.getLogger("simplevk")


class Bot:
    def __init__(
        self,
        token: str,
        rules: dict[str, type[BaseRule]] | None = None,
        *,
        group_id: int | None = None,
        max_threads: int = 32,
        error_handler: Callable[[Exception, VkBotEvent | None], Any] | None = None,
    ):
        self.token = token
        self.rules = rules or BASE_RULES
        self.error_handler = error_handler or base_error_handler

        self.session = RobustVkApi(token=self.token)
        self.api = self.session.get_api()
        self.uploader = vk_api.VkUpload(self.api)
        if group_id is None:
            self.group_id: int = self.api.groups.getById()["groups"][0]["id"]
        else:
            self.group_id = group_id
        self.longpoll = RobustLongPoll(self.session, self.group_id)
        self.longpoll.session = self.session.http

        self.labeler = BotLabeler(self, self.rules)

        self.cb_server: CallbackServer | None = None
        self._event_ids = LimitedDict(size_limit=150)
        self.lock = Lock()

        self.executor = ThreadPoolExecutor(
            max_workers=max_threads, thread_name_prefix=f"EventHandler_{self.group_id}"
        )

    def set_callback(
        self,
        secret_key: str,
        host: str = "127.0.0.1",
        port: int = 8080,
        path: str = "/",
    ):
        if not path.startswith("/"):
            path = "/" + path

        self.cb_server = CallbackServer(self, host, port, path, secret_key)
        logger.info(f"Callback server configured at http://{host}:{port}{path}")

    def handle_events(self, raw_event: VkBotEvent | VkBotMessageEvent, source: str):
        with self.lock:
            event_id = raw_event.raw["event_id"]
            if event_id not in self._event_ids:
                self._event_ids[event_id] = source
            else:
                self._event_ids.pop(event_id, None)
                return

        if not (event_type := events.get(raw_event.type)):
            return

        try:
            event = event_type(raw_event, self)
            self.labeler.check(event)
        except Exception as err:
            self.error_handler(err, raw_event)

    @property
    def sent(self) -> SentMessage:
        return SentMessage(self.api, group_id=self.group_id)

    @property
    def on(self) -> BotLabeler:
        return self.labeler

    def listen(self):
        logger.info("Longpoll listen started.")
        current_delay = 1
        max_delay = 30

        while True:
            try:
                for event in self.longpoll.check():
                    self.executor.submit(self.handle_events, event, "lp")

                current_delay = 1

            except (Timeout, ReadTimeoutError):
                pass

            except Exception as err:
                self.error_handler(err, None)

                time.sleep(current_delay)
                current_delay = min(current_delay * 2, max_delay)

    def start_listen(self, *, join_lp: bool = True, print_banner: bool = True):
        if self.longpoll.url is None:
            self.longpoll.update_longpoll_server()

        lp = Thread(target=self.listen, name="Longpoll", daemon=True)
        lp.start()

        if self.cb_server:
            self.cb_server.start()

        if print_banner:
            print(f"\n🚀 Bot started\n🤖 Group: https://vk.ru/club{self.group_id}")
            if self.cb_server:
                url = f"http://{self.cb_server.host}:{self.cb_server.port}{self.cb_server.path}"
                print(f"📡 Callback Server running at: {url}")
            print("🛑 Press Ctrl+C to stop\n")

        if join_lp:
            try:
                while lp.is_alive():
                    lp.join(0.1)
            except KeyboardInterrupt:
                if print_banner:
                    print("\n👋 Stopping bot...")
                logger.info("Stopping bot (Ctrl+C)...")

                if self.cb_server:
                    self.cb_server.stop()

                self.executor.shutdown(wait=False)
