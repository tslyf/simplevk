import orjson

from simplevk.bot.api import RobustVkApi

from .widgets import BaseWidget


class WidgetApi:
    def __init__(self, token: str):
        self.token = token
        self.api = RobustVkApi(token).get_api()

    def update(self, widget: BaseWidget):
        self.api.appWidgets.update(
            code=f"return {orjson.dumps(widget.dict).decode()};",
            type=widget.type,
        )
