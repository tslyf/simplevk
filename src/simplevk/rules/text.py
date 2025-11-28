from __future__ import annotations

import re
import typing

from simplevk.events import Message

from .base import BaseRule

if typing.TYPE_CHECKING:
    from simplevk.events.base import BaseEvent


class ReRule(BaseRule):
    __slots__ = ("regexp",)

    def __init__(self, regexp: str | list):
        flags = re.IGNORECASE
        if isinstance(regexp, str):
            self.regexp = [re.compile(regexp, flags)]
        elif isinstance(regexp, list):
            self.regexp = [re.compile(i, flags) for i in regexp]

    def check(self, event: BaseEvent, **kwargs) -> bool | dict:
        if not isinstance(event, Message):
            return False
        for regexp in self.regexp:
            match = re.match(regexp, event.text)
            if match:
                return match.groupdict() or {"match": match.groups()}
        return False


class TextRule(BaseRule):
    __slots__ = ("text",)

    def __init__(self, text: str | list) -> None:
        if isinstance(text, str):
            self.text = [text.lower()]
        elif isinstance(text, list):
            self.text = [i.lower() for i in text]

    def check(self, event: BaseEvent, **kwargs) -> bool | dict:
        if not isinstance(event, Message):
            return False
        for text in self.text:
            if event.text.strip().lower() == text:
                return True
        return False
