import typing

from .base import BaseEvent

if typing.TYPE_CHECKING:
    from vk_api.bot_longpoll import VkBotEvent

    from simplevk.bot import Bot


class GroupLeave(BaseEvent):
    __slots__ = ("user_id", "self")

    def __init__(self, event: "VkBotEvent", bot: "Bot"):
        super().__init__(event, bot)

        self.user_id: int = event.obj["user_id"]
        self.self: bool = bool(event.obj["self"])


class GroupJoin(BaseEvent):
    __slots__ = ("user_id", "join_type")

    def __init__(self, event: "VkBotEvent", bot: "Bot"):
        super().__init__(event, bot)

        self.user_id: int = event.obj["user_id"]
        self.join_type: str = event.obj["join_type"]


class UserBlock(BaseEvent):
    __slots__ = ("admin_id", "user_id", "unblock_date", "reason", "comment")

    def __init__(self, event: "VkBotEvent", bot: "Bot"):
        super().__init__(event, bot)

        self.admin_id: int = event.obj["admin_id"]
        self.user_id: int = event.obj["user_id"]
        self.unblock_date: int = event.obj["unblock_date"]
        self.reason: int = event.obj["reason"]
        self.comment: str = event.obj["comment"]


class UserUnblock(BaseEvent):
    __slots__ = ("admin_id", "user_id", "by_end_date")

    def __init__(self, event: "VkBotEvent", bot: "Bot"):
        super().__init__(event, bot)

        self.admin_id: int = event.obj["admin_id"]
        self.user_id: int = event.obj["user_id"]
        self.by_end_date: int = event.obj["by_end_date"]
