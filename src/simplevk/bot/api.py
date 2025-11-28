import logging
import random
import time
from typing import Any, Callable

import orjson
from requests import HTTPError, Session
import requests
from vk_api import ApiError, VkApi
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.vk_api import VkApiMethod as oVkApiMethod

logger = logging.getLogger(__name__)


class VkApiMethod(oVkApiMethod):
    _vk: "RobustVkApi"

    def get_id(self):
        return self._vk.get_id()


class RobustVkApi(VkApi):
    def __init__(
        self,
        token: str | None = None,
        api_version: str = "5.245",
        session: "Session | None" = None,
    ):
        self.token = {"access_token": token}
        self.api_version = api_version

        self._error_retries: dict[tuple[int, str], int] = {}

        self.error_handlers: dict[int, Callable[[ApiError], Any | None]] = {
            6: self.too_many_rps_handler,
            10: self._create_retry_handler(max_retries=5),
            22: self._create_retry_handler(max_retries=5),
            29: self._create_retry_handler(max_retries=5),
        }

        self.http = session or Session()
        if not session:
            self.http.headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
            }

        self._id: int | None = None

    def get_id(self) -> int:
        if self._id is not None:
            return self._id

        users = self.method("users.get")
        if users and isinstance(users, list) and users[0].get("id"):
            self._id = int(users[0]["id"])
            return self._id
        
        groups = self.method("groups.getById")["groups"]
        if groups and isinstance(groups, list) and groups[0].get("id"):
            self._id = -int(groups[0]["id"])
            return self._id
        
        raise ValueError("Failed to get user or group ID")

    def too_many_rps_handler(self, error: ApiError):
        time.sleep(0.4)
        return error.try_method()

    def _create_retry_handler(self, max_retries: int, initial_delay: float = 0.3):
        def handler(error: ApiError):
            error_key = (error.code, error.method)
            current_retries = self._error_retries.get(error_key, 0)

            if current_retries >= max_retries:
                self._error_retries.pop(error_key, None)
                logger.error(
                    f"Max retries reached for method '{error.method}' with code {error.code}."
                )
                raise error

            delay = initial_delay * (1.5 ** current_retries) + random.uniform(0.1, 0.5)
            delay = min(delay, 3)

            logger.warning(
                f"VK Error {error.code} on '{error.method}'. "
                f"Retry {current_retries + 1}/{max_retries}. "
                f"Wait {delay:.2f}s..."
            )
            time.sleep(delay)

            self._error_retries[error_key] = current_retries + 1

            return error.try_method()

        return handler

    def get_api(self):
        return VkApiMethod(self)

    def request(
        self,
        url: str,
        *,
        values: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float = 30,
        verify: bool = True,
        **kwargs: Any,
    ) -> Any:
        max_retries = 5
        delay = 0.5
        last_error: Exception | None = None

        for retry in range(max_retries):
            try:
                response = self.http.post(
                    url,
                    data=values,
                    params=params,
                    timeout=timeout,
                    verify=verify,
                    **kwargs,
                )

                if response.status_code in (502, 503, 504):
                    raise requests.HTTPError(f"Server Error {response.status_code}")

                response.raise_for_status()
                return orjson.loads(response.content)
            
            except (requests.RequestException, orjson.JSONDecodeError) as e:
                last_error = e
                if retry == max_retries - 1:
                    break
                
                logger.warning(
                    f"Request error on '{url}': {e}. "
                    f"Retry {retry + 1}/{max_retries} in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay = min(delay * 1.5 + random.uniform(0, 0.5), 5.0)
                continue
            
        if last_error:
            raise last_error
        
        raise Exception("Request failed with unknown error")

    def method(
        self,
        method: str,
        values: dict[str, Any] | None = None,
        captcha_sid: int | str | None = None,
        captcha_key: str | None = None,
        raw: bool = False,
        with_cookies: bool = False,
    ):
        values = values.copy() if values else {}
        values.setdefault("v", self.api_version)
        verify = values.pop("verify", None)
        if self.token:
            values["access_token"] = self.token["access_token"]

        if captcha_sid and captcha_key:
            values["captcha_sid"] = captcha_sid
            values["captcha_key"] = captcha_key

        try:
            response_data = self.request(
                f"https://api.vk.ru/method/{method}",
                values=values,
                verify=verify,
                timeout=30,
            )
        except HTTPError as e:
            logger.error(f"HTTP Error executing method {method}: {e}")
            raise e

        if "error" in response_data:
            error = ApiError(self, method, values, raw, response_data["error"])
            if error.code in self.error_handlers:
                response_data = self.error_handlers[error.code](error)
                if response_data is not None:
                    return response_data

            raise error

        for code in self.error_handlers.keys():
            self._error_retries.pop((code, method), None)

        return response_data if raw else response_data["response"]


class RobustLongPoll(VkBotLongPoll):
    def __init__(self, vk: RobustVkApi, group_id: int, wait: int = 25):
        self.vk = vk
        self.group_id = group_id
        self.wait = wait

        self.url: str | None = None
        self.key: str | None = None
        self.server: str | None = None
        self.ts: int | None = None

        self.session = Session()

    def check(self):
        values = {
            "act": "a_check",
            "key": self.key,
            "ts": self.ts,
            "wait": self.wait,
        }

        assert self.url is not None

        response = self.vk.request(
            self.url,
            params=values,
            timeout=self.wait + 5,
        )

        if "failed" not in response:
            self.ts = response["ts"]
            return [self._parse_event(raw_event) for raw_event in response["updates"]]

        elif response["failed"] == 1:
            self.ts = response["ts"]

        elif response["failed"] == 2:
            self.update_longpoll_server(update_ts=False)

        elif response["failed"] == 3:
            self.update_longpoll_server()

        return []

    @classmethod
    def _cls_parse_event(cls, raw_event: dict):
        event_class = cls.CLASS_BY_EVENT_TYPE.get(
            raw_event["type"], cls.DEFAULT_EVENT_CLASS
        )
        return event_class(raw_event)

    def _parse_event(self, raw_event: dict):
        return self._cls_parse_event(raw_event)
