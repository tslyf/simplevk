from __future__ import annotations

from typing import TYPE_CHECKING

from simplevk import events
from simplevk.rules import BaseRule

from .base_labeler import BaseLabeler
from .command.labeler import CommandLabeler

if TYPE_CHECKING:
    from simplevk.bot.bot import Bot
    from simplevk.events import BaseEvent

MessageLabeler = BaseLabeler
MessageEventLabeler = BaseLabeler
GroupJoinLabeler = BaseLabeler
GroupLeaveLabeler = BaseLabeler
UserBlockLabeler = BaseLabeler
UserUnblockLabeler = BaseLabeler


class BotLabeler:
    __slots__ = (
        "bot",
        "custom_rules",
        "types",
        "message",
        "message_event",
        "command",
        "group_join",
        "group_leave",
        "user_block",
        "user_unblock",
    )

    def __init__(
        self, bot: "Bot", custom_rules: dict[str, type[BaseRule]] | None = None
    ):
        self.bot = bot
        self.custom_rules = custom_rules or {}
        self.types: dict[type[events.BaseEvent], str] = {
            events.Message: "message",
            events.MessageEvent: "message_event",
            events.GroupJoin: "group_join",
            events.GroupLeave: "group_leave",
            events.UserBlock: "user_block",
            events.UserUnblock: "user_unblock",
        }

        self.message = MessageLabeler(self.custom_rules)
        self.message_event = MessageEventLabeler(self.custom_rules)
        self.command = CommandLabeler(self.bot, self.custom_rules)

        self.group_join = GroupJoinLabeler()
        self.group_leave = GroupLeaveLabeler()
        self.user_block = UserBlockLabeler()
        self.user_unblock = UserUnblockLabeler()

    def start(self):
        def decorator(func):
            func = self.message("private", payload={"command": "start"})(func)
            func = self.message("private", text=["старт", "start", "начать"])(func)
            return func

        return decorator

    def __getitem__(self, name: type[BaseEvent] | str) -> BaseLabeler | None:
        _name = None
        if isinstance(name, type):
            _name = self.types.get(name)
        if not _name:
            return None
        return getattr(self, _name, None)

    @property
    def get(self):
        return self.__getitem__

    def check(self, event: BaseEvent):
        if isinstance(event, events.Message):
            if self.command.check(event) is not False:
                return

        labeler = self.get(type(event))
        if not labeler:
            return

        labeler.check(event)
