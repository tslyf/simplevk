from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from re import Pattern
from types import EllipsisType
from typing import TYPE_CHECKING, Any, Callable

from simplevk.events.message import Message
from simplevk.labeler.base_labeler import BaseLabeler, Handler

from .errors import ValidationError
from .parser import ParamInfo, parse_signature

if TYPE_CHECKING:
    from simplevk.bot import Bot
    from simplevk.events.base import BaseEvent
    from simplevk.rules import BaseRule

logger = logging.getLogger(__name__)


@dataclass
class CommandHandler(Handler):
    name: Pattern[str] | EllipsisType
    args: list[ParamInfo] = field(default_factory=list)
    strict: bool = False
    ignore_return: bool = False


class CommandLabeler(BaseLabeler):
    def __init__(
        self, bot: "Bot", custom_rules: dict[str, type[BaseRule]] | None = None
    ):
        super().__init__(custom_rules)
        self.bot = bot
        self.command_handlers: list[CommandHandler] = []

        self.prefixes_factory: Callable[
            [Message, dict[str, Any]], list[str | Pattern[str]] | None
        ] = self._default_prefixes_factory
        self.bot_mention: Pattern[str] = re.compile(rf"\[club{self.bot.group_id}\|.+?\],?")
        self.validation_error_handler: (
            Callable[[Message, ValidationError, CommandHandler, ParamInfo], Any] | None
        ) = self._default_validation_error_handler

    def _default_prefixes_factory(
        self, message: Message, from_middlewares: dict[str, Any]
    ) -> list[str | Pattern[str]] | None:
        prefixes: list[str | Pattern[str]] = ["/", "!", self.bot_mention]
        if not message.from_chat:
            prefixes.append("")
        return prefixes

    def _default_validation_error_handler(
        self,
        message: Message,
        error: ValidationError,
        handler: CommandHandler,
        param: ParamInfo,
    ) -> Any:
        message.answer(
            f"⚠️ Неверное использование команды. {param.name}: {error.reason}"
        )

    def __call__(
        self,
        *checks: str | BaseRule,
        name: str | EllipsisType,
        strict: bool = False,
        ignore_return: bool = False,
        **rules: Any,
    ):
        def decorator(func: Callable):
            parsed_args = parse_signature(func, strict)

            rules_list = []
            for rule_name, rule_arg in rules.items():
                rules_list.append(self.resolve_rule(rule_name, rule_arg))

            final_name = name
            if final_name is not ...:
                final_name = re.compile(rf"^{final_name}(?:\s+|$)", re.IGNORECASE)

            handler = CommandHandler(
                func=func,
                rules=rules_list,
                name=final_name,
                args=parsed_args,
                strict=strict,
                ignore_return=ignore_return,
            )
            self.command_handlers.append(handler)
            return func

        return decorator

    def check(self, event: BaseEvent):
        if not isinstance(event, Message):
            return

        from_middlewares, _middleware_time = self._check_middlewares(event)
        if from_middlewares is False:
            return False

        text = event.text
        if prefixes := self.prefixes_factory(event, from_middlewares):
            prefixes_str: list[str] = []
            for p in prefixes:
                p_str = p.pattern if isinstance(p, Pattern) else re.escape(p)
                prefixes_str.append(p_str.removeprefix("^"))
            prefixes_regex = re.compile(
                rf"^({'|'.join(prefixes_str)})\s*", re.IGNORECASE
            )

            match = prefixes_regex.match(text)
            if not match:
                return False

            text = text[match.end() :]

        candidates: list[tuple[CommandHandler, dict[str, Any], str]] = []
        for handler in self.command_handlers:
            args = text
            if handler.name is not ... and (match := handler.name.match(text)):
                args = text[match.end() :]
            elif handler.name is not ...:
                continue

            check_res = handler.check(event, from_middlewares)
            if check_res is not False:
                candidates.append((handler, check_res, args.strip()))

        if not candidates:
            return False

        last_error: tuple[ValidationError, CommandHandler, ParamInfo] | None = None
        for handler, check_res, args in candidates:
            call_kwargs = {**check_res, **from_middlewares}
            remaining_args = args
            candidate_failed = False

            for param in handler.args:
                arg_def = param.arg

                try:
                    call_kwargs[param.name], remaining_args = arg_def.parse(
                        remaining_args, event
                    )
                    remaining_args = remaining_args.strip()
                except ValidationError as e:
                    if handler.name is not ...:
                        last_error = (e, handler, param)

                    if param.default is not ...:
                        call_kwargs[param.name] = param.default
                        continue

                    candidate_failed = True
                    break

            if candidate_failed:
                continue

            result = self._execute_handler(
                handler, event, call_kwargs, from_middlewares, _middleware_time
            )

            if not handler.ignore_return and isinstance(result, str):
                event.answer(result)
            
            elif not handler.ignore_return and result is not None:
                _name = (
                    handler.name.pattern
                    if isinstance(handler.name, Pattern)
                    else handler.name
                )
                raise ValueError(f"Command {_name} returned non-string value: {result}")

            return

        if (
            last_error
            and self.validation_error_handler is not None
        ):
            self.validation_error_handler(
                event,
                last_error[0],
                last_error[1],
                last_error[2],
            )
            return

        return False
