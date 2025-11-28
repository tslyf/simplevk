import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, Generic, TypeVar, overload

from cachebox import TTLCache, cached

from simplevk.events import Message

from .errors import ValidationError

if TYPE_CHECKING:
    from simplevk.bot import Bot


_NUMBER_REGEX = re.compile(r"^(\d+(?:[\.,]\d+)?)(?:\s+|$)")
_MENTION_REGEX = re.compile(r"^\[(id|club|public)(\d+)\|.*?\](?:\s+|$)", re.IGNORECASE)
_SCREEN_NAME_REGEX = re.compile(
    r"^(?:https?://)?vk\.(?:com|me|ru)/([a-zA-Z0-9_.]+)(?:[^\s]*)?(?:\s+|$)",
    re.IGNORECASE,
)

Variant = str | int | float | re.Pattern[str]
T = TypeVar("T", bound=Variant | Enum)
E = TypeVar("E", bound=Enum)

BOOLEAN_CHOICES: dict[bool, list[Variant] | Variant] = {
    True: [
        re.compile(r"1|y(es)?|true|on|enabled?|да|lf|ок|вкл(ючить)?|\+"),
    ],
    False: [
        re.compile(r"0|n(o)?|false|off|disabled?|нет?|ytn|выкл(ючить)?|"),
    ],
}


def _cache_key(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Any, ...]:
    return (kwargs.get("screen_name") or args[2],)


@dataclass(unsafe_hash=True)
class Arg(ABC):
    @abstractmethod
    def parse(self, value: str, message: Message) -> tuple[Any, str]: ...


@dataclass(slots=True)
class ParamInfo:
    arg: Arg
    name: str
    default: Any = ...
    description: str | None = None


@dataclass(slots=True)
class ParamStub:
    arg: Arg | type[Arg] | None = None
    default: Any = ...
    name: str | None = None
    description: str | None = None


def Param(
    arg: Arg | type[Arg] | None = None,
    default: Any = ...,
    description: str | None = None,
) -> Any:
    return ParamStub(arg, default, description=description)


@dataclass(slots=True, unsafe_hash=True)
class StringArg(Arg):
    greedy: bool = False
    allow_quotes: bool = True

    def parse(self, value: str, message: Message) -> tuple[str, str]:
        if not value:
            raise ValidationError(value, "Отсутствует значение")

        if self.greedy:
            return value, ""

        if self.allow_quotes and value[0] in ('"', "'"):
            quote_char = value[0]
            end_quote_idx = value.find(quote_char, 1)

            if end_quote_idx == -1:
                raise ValidationError(value, "Незакрытая кавычка")

            parsed_text = value[1:end_quote_idx]
            remaining = value[end_quote_idx + 1 :]
            if remaining.startswith(" "):
                remaining = remaining[1:]
            return parsed_text, remaining

        parts = value.split(" ", 1)
        res = parts[0]
        remaining = parts[1] if len(parts) > 1 else ""

        return res, remaining


@dataclass(slots=True, unsafe_hash=True)
class ChoiceArg(Arg, Generic[T]):
    choices: Any
    ignore_case: bool = True

    _lookup: list[tuple[T, re.Pattern[str]]] = field(init=False, repr=False)

    @overload
    def __init__(
        self: "ChoiceArg[E]", choices: type[E], ignore_case: bool = True
    ) -> None: ...

    @overload
    def __init__(
        self: "ChoiceArg[T]",  # pyright: ignore[reportInvalidTypeVarUse]
        choices: list[T],
        ignore_case: bool = True,
    ) -> None: ...

    @overload
    def __init__(
        self: "ChoiceArg[T]",  # pyright: ignore[reportInvalidTypeVarUse]
        choices: dict[T, list[Variant] | Variant],
        ignore_case: bool = True,
    ) -> None: ...

    def __init__(self, choices: Any, ignore_case: bool = True) -> None:
        self.choices = choices
        self.ignore_case = ignore_case
        self.__post_init__()

    def __post_init__(self):
        self._lookup = []
        raw_map: dict[Any, list[Variant]] = {}

        if isinstance(self.choices, type) and issubclass(self.choices, Enum):
            for member in self.choices:
                raw_map[member] = [member.name, member.value, member.name.lower()]

        elif isinstance(self.choices, dict):
            for ret_value, variants in self.choices.items():
                if not isinstance(variants, list):
                    variants = [variants]
                raw_map[ret_value] = variants

        elif isinstance(self.choices, list):
            for variant in self.choices:
                raw_map[variant] = [variant]
        else:
            raise ValueError(f"Unsupported choices type: {type(self.choices)}")

        flags = re.IGNORECASE if self.ignore_case else 0
        for ret_value, variants in raw_map.items():
            pattern_parts = []
            for choice in variants:
                if not isinstance(choice, (str, int, float, re.Pattern)):
                    raise ValueError(f"Unsupported choice type: {choice}")
                if isinstance(choice, re.Pattern):
                    pattern_parts.append(choice.pattern)
                else:
                    pattern_parts.append(re.escape(str(choice)))

            if not pattern_parts:
                continue

            pattern = rf"^({'|'.join(pattern_parts)})(?:\s+|$)"
            self._lookup.append((ret_value, re.compile(pattern, flags)))

    def parse(self, value: str, message: Message) -> tuple[T, str]:
        if not value:
            raise ValidationError(value, "Отсутствует значение")

        for result_val, pattern in self._lookup:
            if match := pattern.match(value):
                return result_val, value[match.end() :]

        expected = []
        for val, _ in self._lookup:
            if isinstance(val, Enum):
                expected.append(val.value)
            else:
                expected.append(str(val))

        raise ValidationError(value, f"Ожидалось: {', '.join(expected)}")


@dataclass(slots=True, unsafe_hash=True)
class RegexArg(Arg):
    regex: str = field(default=r"[^\s]+")
    ignore_case: bool = True
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self):
        _regex = self.regex
        if not _regex.startswith("^"):
            _regex = f"^{_regex}"
        _regex = _regex.removesuffix("$")
        _regex = rf"{_regex}(?:\s+|$)"
        self._compiled = re.compile(_regex, re.IGNORECASE if self.ignore_case else 0)

    def parse(self, value: str, message: Message) -> tuple[str, str]:
        if not value:
            raise ValidationError(value, "Отсутствует значение")

        match = self._compiled.match(value)
        if not match:
            raise ValidationError(
                f"Не соответствует шаблону «{self.regex}»",
                value,
            )
        if match.groupdict():
            result = list(match.groupdict().values())[0]
        else:
            result = match.group(0)
        return result, value[match.end() :]


@dataclass(slots=True, unsafe_hash=True)
class NumberArg(Arg):
    is_float: bool = False
    min_value: int | float | None = None
    max_value: int | float | None = None

    def parse(self, value: str, message: Message) -> tuple[int | float, str]:
        if not value:
            raise ValidationError(value, "Отсутствует значение")

        try:
            parsed = _NUMBER_REGEX.match(value)
            if not parsed:
                raise ValueError()

            _value = parsed.group(1)
            res = float(_value.replace(",", ".")) if self.is_float else int(_value)
            remaining = value[parsed.end() :]
        except (ValueError, ValidationError):
            msg = (
                "Не является целым числом"
                if not self.is_float
                else "Не является числом с плавающей запятой"
            )
            raise ValidationError(value, msg)

        if self.min_value is not None and res < self.min_value:
            raise ValidationError(
                value, f"Меньше минимального значения {self.min_value}"
            )
        if self.max_value is not None and res > self.max_value:
            raise ValidationError(
                value, f"Больше максимального значения {self.max_value}"
            )
        return res, remaining


@dataclass(slots=True, unsafe_hash=True)
class PeerIDArg(Arg):
    allow_user: bool = True
    allow_group: bool = True

    def __post_init__(self):
        if not self.allow_user and not self.allow_group:
            raise ValueError(
                "allow_user and allow_group cannot be False at the same time"
            )

    @cached(
        TTLCache(maxsize=250, ttl=60 * 60),
        key_maker=_cache_key,
    )
    def _resolve_screen_name(self, bot: "Bot", screen_name: str) -> int | None:
        _resolved_id = None
        try:
            vkuser = bot.api.utils.resolve_screen_name(screen_name=screen_name)
            _resolved_id = int(vkuser["object_id"])
            if vkuser["type"] == "group":
                _resolved_id *= -1
            elif vkuser["type"] != "user":
                return None
        except Exception:
            pass

        return _resolved_id

    def parse(self, value: str, message: Message) -> tuple[int, str]:
        resolved_id: int | None = None
        remaining = value

        if value:
            if match := _MENTION_REGEX.match(value):
                resolved_id = int(match.group(2))
                if match.group(1) in ("club", "public"):
                    resolved_id *= -1
                remaining = value[match.end() :]

            elif match := _SCREEN_NAME_REGEX.match(value):
                screen_name, remaining = match.group(1), value[match.end() :]
                resolved_id = self._resolve_screen_name(message.bot, screen_name)
                if resolved_id is None:
                    raise ValidationError(
                        value,
                        "Ссылка на пользователя или группу недействительна",
                    )

        if (
            resolved_id is None
            or (resolved_id < 0 and not self.allow_group)
            or (resolved_id > 0 and not self.allow_user)
        ):
            if message.reply_message:
                resolved_id = message.reply_message.from_id
            elif message.fwd_messages:
                resolved_id = message.fwd_messages[0].from_id

        if isinstance(resolved_id, int):
            if resolved_id < 0 and not self.allow_group:
                raise ValidationError(
                    value,
                    "Ожидался идентификатор пользователя, но получен идентификатор группы",
                )
            elif resolved_id > 0 and not self.allow_user:
                raise ValidationError(
                    value,
                    "Ожидался идентификатор группы, но получен идентификатор пользователя",
                )

        elif resolved_id is None:
            _targets = []
            if self.allow_user:
                _targets.append("пользователя")
            if self.allow_group:
                _targets.append("группы")
            raise ValidationError(
                value,
                f"Не удалось найти идентификатор {' или '.join(_targets)}",
            )

        return resolved_id, remaining


Integer = Annotated[int, NumberArg()]
Float = Annotated[float, NumberArg(is_float=True)]
PositiveInteger = Annotated[int, NumberArg(min_value=0)]
PositiveFloat = Annotated[float, NumberArg(min_value=0, is_float=True)]
Boolean = Annotated[bool, ChoiceArg(choices=BOOLEAN_CHOICES)]
Word = Annotated[str, StringArg()]
Text = Annotated[str, StringArg(greedy=True)]
PeerID = Annotated[int, PeerIDArg()]
UserID = Annotated[int, PeerIDArg(allow_user=True, allow_group=False)]
GroupID = Annotated[int, PeerIDArg(allow_user=False, allow_group=True)]
