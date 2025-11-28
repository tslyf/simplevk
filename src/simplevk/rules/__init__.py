from .base import BaseRule
from .message import ClientInfoRule, IsChatRule, IsPrivateRule
from .payload import PayloadRule
from .text import ReRule, TextRule

rules: dict[str, type[BaseRule]] = {
    "re": ReRule,
    "text": TextRule,
    "payload": PayloadRule,
    "private": IsPrivateRule,
    "chat": IsChatRule,
    "client": ClientInfoRule,
}

__all__ = (
    "rules",
    "BaseRule",
    "ClientInfoRule",
    "IsChatRule",
    "IsPrivateRule",
    "PayloadRule",
    "ReRule",
    "TextRule",
)
