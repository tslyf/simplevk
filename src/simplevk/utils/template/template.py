import orjson

from simplevk.utils.template.elements import CarouselElement


class Template:
    __slots__ = ("type",)

    def get_json(self) -> str:
        data = {k: v for k in self.__slots__ if (v := getattr(self, k)) is not None}
        data["type"] = self.type
        return orjson.dumps(data).decode()


class Carousel(Template):
    __slots__ = ("elements",)

    def __init__(self):
        self.type = "carousel"
        self.elements: list[dict] = []

    def add(self, element: CarouselElement) -> "Carousel":
        self.elements.append(element.get_dict())
        return self
