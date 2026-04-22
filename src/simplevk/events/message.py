import typing
from dataclasses import dataclass, field

from dacite import from_dict
from vk_api.bot_longpoll import VkBotMessageEvent

from simplevk.events.attachments import (
    DACITE_CONFIG,
    BaseAttachment,
    parse_attachment,
)
from simplevk.objects.messages import SentMessage
from simplevk.utils import parse_json

from .base import BaseEvent

if typing.TYPE_CHECKING:
    from simplevk.bot import Bot
    from simplevk.bot.api import VkApiMethod


@dataclass(kw_only=True)
class ClientInfo:
    button_actions: list[str] = field(default_factory=list)
    keyboard: bool = False
    inline_keyboard: bool = False
    carousel: bool = False
    lang_id: int = 0


class Message(BaseEvent):
    __slots__ = (
        "client_info",
        "group_id",
        "from_id",
        "peer_id",
        "from_chat",
        "from_user",
        "from_group",
        "date",
        "text",
        "payload",
        "expire_ttl",
        "_message_id",
        "conversation_message_id",
        "_full_message",
        "reply_message",
        "fwd_messages",
        "attachments",
        "_event_id",
        "keyboard",
        "template",
        "_answer",
    )

    def __init__(self, event: VkBotMessageEvent | dict, bot: "Bot"):
        super().__init__(event, bot)

        if isinstance(event, VkBotMessageEvent):
            self._event_id = event.raw["event_id"]
            _client_info = event.client_info
            self.group_id = event.group_id
            if event.message is None:
                raise ValueError("Message is required") from None
            event = event.message
        else:
            _client_info = event.get("client_info")
            self.group_id = event.get("group_id")

        self.client_info = (
            from_dict(data_class=ClientInfo, data=_client_info, config=DACITE_CONFIG)
            if _client_info is not None
            else None
        )

        self.from_id: int = event["from_id"]
        self.peer_id: int = event.get("peer_id", 0)
        self.from_chat: bool = self.peer_id > 0 and self.peer_id != self.from_id
        self.from_user: bool = self.from_id > 0
        self.from_group: bool = self.from_id < 0

        self.date: int = event["date"]
        self.text: str = event["text"]
        self.payload = parse_json(event.get("payload"), default={})
        if (
            isinstance(self.payload, dict)
            and self.payload.get("command") == "not_supported_button"
        ):
            if (_payload := parse_json(self.payload.get("payload"))) is not None:
                self.payload = _payload
        self.expire_ttl: int | None = event.get("expire_ttl")

        self._message_id: int | None = event.get("id")
        if self._message_id == 0:
            self._message_id = None
        self.conversation_message_id: int | None = event.get("conversation_message_id")
        self._full_message: Message | None = None

        self.reply_message: Message | None = None
        if reply := event.get("reply_message"):
            self.reply_message = Message(reply, self.bot)
        self.fwd_messages: tuple[Message, ...] = tuple(
            Message(msg, self.bot) for msg in event.get("fwd_messages", [])
        )
        self.attachments: tuple[BaseAttachment, ...] = tuple(
            parsed
            for att in event.get("attachments", [])
            if (parsed := parse_attachment(att)) is not None
        )
        self.keyboard: dict | None = event.get("keyboard")
        self.template: dict | None = event.get("template")

        self._answer = lambda: SentMessage(
            self.bot.api,
            peer_id=self.peer_id,
            group_id=self.bot.group_id,
        ).send

    def get_full_message(self, api: "VkApiMethod | None" = None):
        if self._full_message is not None:
            return self._full_message

        try:
            api = api or self.bot.api
            response = api.messages.getByConversationMessageId(
                peer_id=self.peer_id,
                conversation_message_ids=self.conversation_message_id,
                group_id=self.group_id,
            )["items"][0]
            if self.client_info:
                response["client_info"] = self.client_info.__dict__
            self._full_message = Message(response, self.bot)
        except Exception:
            self._full_message = None
        return self._full_message

    @property
    def message_id(self) -> int | None:
        if self._message_id is not None:
            return self._message_id

        msg = self.get_full_message()
        if msg is None:
            return None
        self._message_id = msg.message_id
        return self._message_id

    def get_list_attachments(self, *, add_access_key: bool = True) -> list:
        parsed_attachments = []
        for attachment in self.attachments:
            owner_id = getattr(attachment, "owner_id", None)
            id_ = getattr(attachment, "id", None)
            access_key = getattr(attachment, "access_key", None)
            if owner_id is None or id is None:
                continue
            parsed_attachments.append(
                f"{attachment.attachment_type}{owner_id}_{id_}"
                + (f"_{access_key}" if add_access_key and access_key else "")
            )
        return parsed_attachments

    @property
    def answer(self):
        return self._answer()

    base_answer = answer
