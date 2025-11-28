from __future__ import annotations

import typing

from simplevk.events import Message, MessageEvent

from .base import BaseRule

if typing.TYPE_CHECKING:
    from simplevk.events.base import BaseEvent


class IsPrivateRule(BaseRule):
    def check(self, event: BaseEvent, **kwargs) -> bool | dict:
        if not isinstance(event, (Message, MessageEvent)):
            return False
        return not event.from_chat


class IsChatRule(BaseRule):
    def check(self, event: BaseEvent, **kwargs) -> bool | dict:
        if not isinstance(event, (Message, MessageEvent)):
            return False
        return event.from_chat


class ClientInfoRule(BaseRule):
    def __init__(self, info: str | tuple):
        if isinstance(info, str):
            self.info = (info,)
        else:
            self.info = info

    def check(self, event: BaseEvent, **kwargs) -> bool | dict:
        if not isinstance(event, (Message, MessageEvent)):
            return False
        if not event.client_info:
            return False
        return all([getattr(event.client_info, i, False) for i in self.info])
