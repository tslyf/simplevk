class BaseAction:
    __slots__ = ("type",)
    type: str

    def get_dict(self) -> dict:
        data = {k: v for k in self.__slots__ if (v := getattr(self, k)) is not None}
        data["type"] = self.type
        return data


class Text(BaseAction):
    __slots__ = ("label", "payload")

    def __init__(self, label: str, payload: dict | str = None):
        self.type = "text"
        self.label = label
        self.payload = payload


class OpenLink(BaseAction):
    __slots__ = ("link", "label", "payload")

    def __init__(self, link: str, label: str, payload: dict | str = None):
        self.type = "open_link"
        self.link = link
        self.label = label
        self.payload = payload


class Location(BaseAction):
    __slots__ = ("payload",)

    def __init__(self, payload: dict | str = None):
        self.type = "location"
        self.payload = payload


class VKPay(BaseAction):
    __slots__ = ("payload", "hash")

    def __init__(self, payload: dict | str = None, hash: str | None = None):
        self.type = "vkpay"
        self.payload = payload
        self.hash = hash


class VKApps(BaseAction):
    __slots__ = ("app_id", "owner_id", "payload", "label", "hash")

    def __init__(
        self,
        app_id: int,
        owner_id: int,
        payload: dict | str = None,
        label: str | None = None,
        hash: str | None = None,
    ):
        self.type = "open_app"
        self.app_id = app_id
        self.owner_id = owner_id
        self.payload = payload
        self.label = label
        self.hash = hash


class Callback(BaseAction):
    __slots__ = ("label", "payload")

    def __init__(self, label: str, payload: dict | str):
        self.type = "callback"
        self.label = label
        self.payload = payload


class IntentSubscribe(BaseAction):
    __slots__ = ("label", "peer_id", "intent", "subscribe_id")

    def __init__(self, label: str, peer_id: int, intent: str, subscribe_id: int):
        self.type = "intent_subscribe"
        self.label = label
        self.peer_id = peer_id
        self.intent = intent
        self.subscribe_id = subscribe_id


class IntentUnsubscribe(BaseAction):
    __slots__ = ("label", "peer_id", "intent", "subscribe_id")

    def __init__(self, label: str, peer_id: int, intent: str, subscribe_id: int):
        self.type = "intent_unsubscribe"
        self.label = label
        self.peer_id = peer_id
        self.intent = intent
        self.subscribe_id = subscribe_id


class KeyboardButton:
    __slots__ = ("action", "color")

    def __init__(self, action: BaseAction, color: str | None = None):
        self.action = action
        self.color = color

    def get_dict(self) -> dict:
        data = {"action": self.action.get_dict()}
        if self.action.type in ["text", "callback"] and self.color:
            data["color"] = self.color
        return data
