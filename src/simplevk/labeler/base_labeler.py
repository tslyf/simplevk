import time
from collections import defaultdict
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Any, Callable, Literal

from simplevk.events import BaseEvent
from simplevk.middlewares import BaseMiddleware
from simplevk.rules import BaseRule
from simplevk.utils.functions import call_with_allowed_args


@dataclass(slots=True)
class Handler:
    func: Callable
    rules: list[BaseRule]

    def check(self, event: BaseEvent, from_middlewares: dict[str, Any] | None = None):
        from_middlewares = from_middlewares or {}

        args: dict[str, Any] = {}
        for rule in self.rules:
            checked = rule.check(event, **from_middlewares)
            if isinstance(checked, dict):
                args.update(checked)
            elif not checked:
                return False

        return args


class BaseLabeler:
    __slots__ = ("handlers", "custom_rules", "middlewares")

    def __init__(self, custom_rules: dict[str, type[BaseRule]] | None = None):
        self.handlers: defaultdict[str, list[Handler]] = defaultdict(list)
        self.custom_rules: dict[str, type[BaseRule]] = custom_rules or {}
        self.middlewares: list[BaseMiddleware] = []

    def register_middleware(
        self, middleware: type[BaseMiddleware] | BaseMiddleware
    ) -> BaseMiddleware:
        if isinstance(middleware, type) and issubclass(middleware, BaseMiddleware):
            middleware = middleware()
            self.middlewares.append(middleware)
        elif isinstance(middleware, BaseMiddleware):
            self.middlewares.append(middleware)
        return middleware

    def resolve_rule(self, rule: str | BaseRule, arg: Any = None) -> BaseRule:
        if isinstance(rule, BaseRule):
            return rule

        rule_cls = self.custom_rules.get(rule)
        if not rule_cls:
            raise ValueError(f"Rule '{rule}' not found in custom_rules")

        return rule_cls(arg) if arg is not None else rule_cls()

    def handle(self, *checks: str | BaseRule, **rules: Any):
        rules_ = []
        for rule in checks:
            rules_.append(self.resolve_rule(rule))

        for rule_name, rule_arg in rules.items():
            rules_.append(self.resolve_rule(rule_name, rule_arg))

        def decorator(func: Callable):
            module_name = Path(func.__code__.co_filename).parts[-1].replace(".py", "")
            self.handlers[module_name].append(Handler(func, rules_))
            return func

        return decorator

    def _check_middlewares(
        self, event: BaseEvent
    ) -> tuple[dict[str, Any] | Literal[False], float]:
        from_middlewares = {}
        _start_time = time.perf_counter()

        for middleware in self.middlewares:
            response = middleware.pre(event)
            if response is False:
                return False, time.perf_counter() - _start_time

            elif isinstance(response, dict):
                from_middlewares.update(response)

        return from_middlewares, time.perf_counter() - _start_time

    def check(self, event: BaseEvent):
        from_middlewares, _middleware_time = self._check_middlewares(event)
        if from_middlewares is False:
            return False

        for handler in chain(*tuple(self.handlers.values())):
            args = {}

            checked = handler.check(event, from_middlewares)
            if isinstance(checked, dict):
                args.update(checked)

            if checked is not False:
                self._execute_handler(
                    handler, event, args, from_middlewares, _middleware_time
                )
                break

    def _execute_handler(
        self,
        handler: Handler,
        event: BaseEvent,
        args: dict[str, Any],
        from_middlewares: dict[str, Any],
        mw_time: float,
    ):
        args.update({
            "middleware_time": mw_time * 1000,
            "execution_time": (time.perf_counter() - event._perf_received_at - mw_time)
            * 1000,
        })
        args.update(from_middlewares)

        result = call_with_allowed_args(handler.func, event, **args)

        for middleware in reversed(self.middlewares):
            middleware.post(event)

        return result

    def __call__(self, *checks: str | BaseRule, **rules: Any):
        return self.handle(*checks, **rules)
