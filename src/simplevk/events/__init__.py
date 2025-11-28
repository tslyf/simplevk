from vk_api.bot_longpoll import VkBotEventType

from .base import BaseEvent
from .group_actions import GroupJoin, GroupLeave, UserBlock, UserUnblock
from .message import ClientInfo, Message
from .message_event import MessageEvent

events: dict[VkBotEventType, type[BaseEvent]] = {
    VkBotEventType.MESSAGE_NEW: Message,
    VkBotEventType.MESSAGE_EVENT: MessageEvent,
    VkBotEventType.GROUP_JOIN: GroupJoin,
    VkBotEventType.GROUP_LEAVE: GroupLeave,
    VkBotEventType.USER_BLOCK: UserBlock,
    VkBotEventType.USER_UNBLOCK: UserUnblock,
}

__all__ = (
    "events",
    "BaseEvent",
    "GroupJoin",
    "GroupLeave",
    "UserBlock",
    "UserUnblock",
    "Message",
    "MessageEvent",
    "ClientInfo",
)
