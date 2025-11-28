import typing

import orjson
from dacite import from_dict
from vk_api.bot_longpoll import VkBotEvent

from simplevk.events.attachments import DACITE_CONFIG
from simplevk.events.message import ClientInfo, Message
from simplevk.objects.messages import SentMessage

from .base import BaseEvent

if typing.TYPE_CHECKING:
    from simplevk.bot import Bot


class MessageEvent(BaseEvent):
    __slots__ = (
        "api",
        "client_info",
        "from_id",
        "peer_id",
        "from_chat",
        "from_user",
        "payload",
        "_message_id",
        "conversation_message_id",
        "event_id",
        "_full_message",
        "_answer",
        "_edit",
    )

    def __init__(self, event: VkBotEvent | dict, bot: "Bot"):
        super().__init__(event, bot)

        if isinstance(event, VkBotEvent):
            _client_info = event.client_info
            event = event.object
        else:
            _client_info = event.get("client_info")

        self.client_info = (
            from_dict(data_class=ClientInfo, data=_client_info, config=DACITE_CONFIG)
            if _client_info is not None
            else None
        )

        self.from_id: int = event["user_id"]
        self.peer_id: int = event["peer_id"]
        self.from_chat: bool = self.peer_id != self.from_id
        self.from_user: bool = self.from_id > 0

        self.payload: dict | str | None = event.get("payload")

        self._message_id: int | None = event.get("id")
        if self._message_id == 0:
            self._message_id = None
        self.conversation_message_id: int | None = event.get("conversation_message_id")
        self.event_id = event["event_id"]
        self._full_message = None

        self._answer = lambda: SentMessage(
            self.bot.api,
            peer_id=self.peer_id,
            group_id=self.bot.group_id,
        ).send
        self._edit = lambda: SentMessage(
            self.bot.api,
            peer_id=self.peer_id,
            group_id=self.bot.group_id,
            conversation_message_id=self.conversation_message_id,
        ).edit

    @property
    def message_id(self) -> int | None:
        if self._message_id is not None:
            return self._message_id

        response = self.bot.api.messages.getByConversationMessageId(
            peer_id=self.peer_id,
            conversation_message_ids=self.conversation_message_id,
        )["items"]
        if not response:
            return None
        message_id: int = response[0]["id"]
        self._message_id = message_id
        return self._message_id

    @property
    def full_message(self) -> Message:
        if self._full_message is None:
            self._full_message = Message(
                self.bot.api.messages.getByConversationMessageId(
                    peer_id=self.peer_id,
                    conversation_message_ids=self.conversation_message_id,
                )["items"][0],
                self.bot,
            )
        return self._full_message

    def event_answer(self, data: dict) -> None:
        self.bot.api.messages.sendMessageEventAnswer(
            event_id=self.event_id,
            user_id=self.from_id,
            peer_id=self.peer_id,
            event_data=orjson.dumps(data).decode(),
        )

    def show_snackbar(self, text: str):
        self.event_answer({"type": "show_snackbar", "text": text})

    def open_link(self, link: str):
        self.event_answer({"type": "open_link", "link": link})

    @property
    def answer(self):
        return self._answer()

    @property
    def edit(self):
        return self._edit()

    base_answer = show_snackbar
