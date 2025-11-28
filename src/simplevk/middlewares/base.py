from __future__ import annotations

from abc import ABC, abstractmethod

from simplevk.events import BaseEvent


class BaseMiddleware(ABC):
    @abstractmethod
    def pre(self, event: BaseEvent) -> bool | dict: ...

    @abstractmethod
    def post(self, event: BaseEvent) -> None: ...
