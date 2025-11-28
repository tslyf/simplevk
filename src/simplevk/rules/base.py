from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from simplevk.events.base import BaseEvent


class BaseRule(ABC):
    def __init__(self, *args: Any, **kwargs: Any): ...

    @abstractmethod
    def check(self, event: BaseEvent, **kwargs: Any) -> bool | dict[str, Any]: ...
