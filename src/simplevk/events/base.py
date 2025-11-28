import time
import typing
from abc import ABC, abstractmethod

from vk_api.bot_longpoll import VkBotEvent, VkBotMessageEvent

if typing.TYPE_CHECKING:
    from simplevk.bot import Bot


class BaseEvent(ABC):
    __slots__ = ("bot", "received_at", "_perf_received_at")

    bot: "Bot"
    received_at: float
    _perf_received_at: float

    @abstractmethod
    def __init__(
        self, event: VkBotMessageEvent | VkBotEvent | dict, bot: "Bot"
    ) -> None:
        self.bot = bot
        self.received_at = time.time()
        self._perf_received_at = time.perf_counter()

    @property
    def _dict(self) -> dict:
        _ret = getattr(self, "__dict__", None)
        if _ret is None:
            _ret = {k: getattr(self, k, None) for k in self.__slots__}
        return _ret

    def __str__(self):
        _vars = self._dict.copy()
        _vars.pop("bot", None)
        _vars = ", ".join([
            f"{k}={repr(v)}" for k, v in _vars.items() if not k.startswith("_")
        ])
        return f"{type(self).__name__}({_vars})"

    __repr__ = __str__
