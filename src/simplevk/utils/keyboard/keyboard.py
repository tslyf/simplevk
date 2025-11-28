import orjson

from .buttons import (
    BaseAction,
    Callback,
    IntentSubscribe,
    IntentUnsubscribe,
    KeyboardButton,
    Location,
    OpenLink,
    Text,
    VKApps,
    VKPay,
)
from .colors import ButtonColor


class Keyboard:
    __slots__ = ("one_time", "inline", "buttons")

    def __init__(self, one_time: bool = False, inline: bool = False):
        self.one_time = one_time
        self.inline = inline
        self.buttons: list[list[KeyboardButton]] = []

    def row(self) -> "Keyboard":
        if len(self.buttons) and not len(self.buttons[-1]):
            raise RuntimeError("Last row is empty!")
        self.buttons.append([])
        return self

    def add(self, action: BaseAction, color: str | None = None) -> "Keyboard":
        if not len(self.buttons):
            self.row()
        button = KeyboardButton(action, color)
        self.buttons[-1].append(button)
        return self

    def add_text(
        self,
        label: str,
        payload: dict | str | None = None,
        color: str = ButtonColor.SECONDARY,
    ):
        return self.add(Text(label, payload), color)

    def add_callback(
        self,
        label: str,
        payload: dict | str | None = None,
        color: str = ButtonColor.SECONDARY,
    ):
        return self.add(Callback(label, payload), color)

    def add_openlink(self, link: str, label: str, payload: dict | str | None = None):
        return self.add(OpenLink(link, label, payload))

    def add_location(self, payload: dict | str | None = None):
        return self.add(Location(payload))

    def add_vkpay(self, payload: dict | str | None = None, hash: str | None = None):
        return self.add(VKPay(payload, hash))

    def add_apps(
        self,
        app_id: int,
        owner_id: int,
        payload: dict | str | None = None,
        label: str | None = None,
        hash: str | None = None,
    ):
        return self.add(VKApps(app_id, owner_id, payload, label, hash))

    def add_subscribe(self, label: str, peer_id: int, intent: str, subscribe_id: int):
        return self.add(IntentSubscribe(label, peer_id, intent, subscribe_id))

    def add_unsubscribe(self, label: str, peer_id: int, intent: str, subscribe_id: int):
        return self.add(IntentUnsubscribe(label, peer_id, intent, subscribe_id))

    def get_json(self) -> str:
        data = orjson.dumps(
            {
                "one_time": self.one_time,
                "inline": self.inline,
                "buttons": [
                    [button.get_dict() for button in row]
                    for row in self.buttons
                    if row
                ],
            }
        ).decode()
        return data

    def __str__(self) -> str:
        return self.get_json()
