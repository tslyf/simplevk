from typing import TYPE_CHECKING, Any

from vk_api.utils import get_random_id

from simplevk.utils.keyboard import Keyboard
from simplevk.utils.template import Carousel

from ..utils.functions import batched

if TYPE_CHECKING:
    from typing import Any

    from simplevk.bot.api import VkApiMethod


class SentMessage:
    api: "VkApiMethod"
    _values: dict[str, Any]

    def __init__(self, api: "VkApiMethod", **kwargs):
        super().__setattr__("api", api)
        super().__setattr__("_values", kwargs)

    @property
    def values(self):
        if isinstance(self._values.get("keyboard"), Keyboard):
            self._values["keyboard"] = self._values["keyboard"].get_json()
        if isinstance(self._values.get("carousel"), Carousel):
            self._values["carousel"] = self._values["carousel"].get_json()
        if self._values.get("message") is not None and not isinstance(
            self._values.get("message"), str
        ):
            self._values["message"] = str(self._values["message"])
        if self._values.get("message_id") is not None and self._values.get(
            "conversation_message_id"
        ):
            self._values.pop("message_id")
        self._values.setdefault("disable_mentions", 1)
        self._values.setdefault("dont_parse_links", 1)
        return self._values

    def _update(self, values: dict):
        values.pop("_api", None)
        values.pop("api", None)
        values.pop("kwargs", None)
        values.pop("self", None)
        values = {k: v for k, v in values.items() if v is not None}
        self._values.update(values)

    def send(
        self,
        message: str | None = None,
        attachment: list[str] | str | None = None,
        keyboard: str | Keyboard | None = None,
        template: str | None = None,
        peer_id: int | None = None,
        **kwargs,
    ):
        api = kwargs.get("_api", self.api)
        self._values["random_id"] = get_random_id()
        self._update(locals())
        self._update(kwargs)
        returned = api.messages.send(**self.values)
        returned["conversation_message_id"] = returned.pop("cmid", None)
        self._update(returned)
        return self

    def edit(
        self,
        message: str | None = None,
        attachment: list[str] | str | None = None,
        keyboard: str | Keyboard | None = None,
        template: str | None = None,
        peer_id: int | None = None,
        **kwargs,
    ):
        if not self.values.get("conversation_message_id") and not self.values.get(
            "message_id"
        ):
            return self
        api = kwargs.get("_api", self.api)
        self._update(locals())
        self._update(kwargs)
        _values = self.values.copy()
        api.messages.edit(**_values)
        return self

    def delete(self):
        assert self.values.get("conversation_message_id"), "no conversation_message_id"
        self.api.messages.delete(
            peer_id=self.values.get("peer_id"),
            cmids=self.values.get("conversation_message_id"),
            delete_for_all=True,
            group_id=self._values.get("group_id"),
        )
        return self

    def add(self, text: str):
        self._update({"message": self._values.get("message", "") + str(text)})
        self.edit(**self.values)
        return self

    def send_many(
        self,
        peer_ids: list[int],
        message: str | None = None,
        attachment: list[str] | None = None,
        keyboard: str | Keyboard | None = None,
        **kwargs,
    ):
        api = kwargs.get("_api", self.api)
        self._values["random_id"] = get_random_id()
        self._update(locals())
        self._update(kwargs)
        self.values.pop("peer_ids", None)
        peer_ids_ = batched(peer_ids, 100)
        for pids in peer_ids_:
            last_err = None
            for _ in range(5):
                try:
                    api.messages.send(peer_ids=pids, **self.values)
                    break
                except Exception as err:
                    last_err = err
                    continue
            else:
                raise Exception(
                    f"Рассылка запнулась, random_id: {self.values['random_id']}, err: {last_err}"
                )

        return self

    @property
    def conversation_message_id(self):
        return self.values.get("conversation_message_id")

    @property
    def message(self):
        return self.values.get("message")

    @message.setter
    def message(self, value):
        self._values["message"] = value

    def __setattr__(self, key, value):
        self._values[key] = value
