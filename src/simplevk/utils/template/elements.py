from simplevk.utils.keyboard.buttons import BaseAction as _BaseAction
from simplevk.utils.keyboard.buttons import KeyboardButton
from simplevk.utils.keyboard.colors import ButtonColor


class BaseAction:
    __slots__ = ("type",)

    def get_dict(self) -> dict:
        data = {k: v for k in self.__slots__ if (v := getattr(self, k)) is not None}
        data["type"] = self.type
        return data


class OpenLink(BaseAction):
    __slots__ = ("link",)

    def __init__(self, link: str):
        self.type = "open_link"
        self.link = link


class OpenPhoto(BaseAction):
    __slots__ = ()

    def __init__(self):
        self.type = "open_photo"


class CarouselElement:
    __slots__ = ("buttons", "title", "description", "photo_id", "action")

    def __init__(
        self,
        title: str | None = None,
        description: str | None = None,
        photo_id: str | None = None,
        action: BaseAction | None = None,
    ):
        self.buttons: list[KeyboardButton] = []
        if not title and not photo_id:
            raise RuntimeError("title or photo_id is required")
        if title and not description:
            description = "..."
        self.title = title
        self.description = description
        self.photo_id = photo_id.replace("photo", "") if photo_id else None
        self.action = action

    def add(
        self,
        action: _BaseAction,
        color: str = ButtonColor.SECONDARY,
    ) -> "CarouselElement":
        self.buttons.append(KeyboardButton(action, color))
        return self

    def get_dict(self) -> dict:
        data = {}
        if self.title is not None:
            data["title"] = self.title
            data["description"] = self.description
        if self.photo_id is not None:
            data["photo_id"] = self.photo_id
        if self.action is not None:
            data["action"] = self.action.get_dict()
        data["buttons"] = [button.get_dict() for button in self.buttons]
        return data
