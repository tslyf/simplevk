from __future__ import annotations

import typing

from simplevk.events import Message, MessageEvent

from .base import BaseRule

if typing.TYPE_CHECKING:
    from simplevk.events.base import BaseEvent


class PayloadRule(BaseRule):
    __slots__ = ("payload", "keys")

    def __init__(self, payload: tuple[dict | str, dict | None] | dict | str) -> None:
        self.payload = {}
        self.keys = []
        if not isinstance(payload, tuple):
            payload = (payload, None)
        if payload:
            self.payload = payload[0]

        self.keys = payload[1].items() if payload[1] else []

    def check(self, event: BaseEvent, **kwargs) -> dict | bool:
        if not isinstance(event, (Message, MessageEvent)):
            return False
        payload = event.payload
        if not payload or type(self.payload) is not type(payload):
            return False

        if isinstance(self.payload, str) or isinstance(payload, str):
            return event.payload == self.payload

        for el in self.payload.items():
            if el not in tuple(payload.items()):
                return False
        args = {}
        for key, tp in self.keys:
            if key not in tuple(payload.keys()) or not isinstance(payload.get(key), tp):
                return False
            args[key] = payload[key]
        return args
