from dataclasses import dataclass, field


class Base:
    @property
    def dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class BaseWidget(Base):
    type: str


@dataclass
class TextWidget(BaseWidget):
    type = "text"

    title: str
    text: str
    title_url: str | None = None
    title_counter: int | None = None
    descr: str | None = None
    more: str | None = None
    more_url: str | None = None


@dataclass
class HeadElement(Base):
    text: str
    align: str | None = None


@dataclass
class BodyElement(Base):
    text: str
    url: str | None = None
    icon_id: str | None = None


@dataclass
class TableWidget(BaseWidget):
    type = "table"

    title: str
    title_url: str | None = None
    title_counter: int | None = None
    head: list[HeadElement] = field(default_factory=list)
    body: list[list[BodyElement]] = field(default_factory=list)
    more: str | None = None
    more_url: str | None = None

    @property
    def dict(self):
        self.__dict__["head"] = [i.dict for i in self.head]
        self.__dict__["body"] = (
            [list(map(lambda x: x.dict, i)) for i in self.body]
            if self.body
            else []
        )

        return super().dict
