import inspect
import time
from collections import OrderedDict
from functools import wraps
from threading import Lock, RLock
from typing import Any, Callable, Mapping, Sequence, TypeVar, overload

import orjson

T = TypeVar("T")
G = TypeVar("G")
K = TypeVar("K")
V = TypeVar("V")


class LimitedDict(OrderedDict[K, V]):
    def __init__(self, *args, size_limit: int | None = None, **kwargs):
        self.size_limit = size_limit
        self._lock = RLock()
        super().__init__(*args, **kwargs)

    def __setitem__(self, key: K, value: V):
        with self._lock:
            super().__setitem__(key, value)
            if self.size_limit is not None:
                while len(self) > self.size_limit:
                    self.popitem(last=False)


@overload
def parse_json(
    obj: None,
    *,
    default: T = None,
    expected_type: type[G] | None = None,
) -> T: ...


@overload
def parse_json(
    obj: str | bytes,
    *,
    default: T = None,
    expected_type: None = None,
) -> Any | T: ...


@overload
def parse_json(
    obj: str | bytes,
    *,
    default: T = None,
    expected_type: type[G],
) -> G | T: ...


def parse_json(
    obj: str | bytes | None,
    *,
    default: T = None,
    expected_type: type[G] | None = None,
) -> Any | G | T:
    if obj is None:
        return default

    try:
        data = orjson.loads(obj)
        return (
            data
            if (expected_type is None or isinstance(data, expected_type))
            else default
        )
    except orjson.JSONDecodeError:
        return default


def batched(seq: Sequence[T], step: int) -> list[tuple[T, ...]]:
    return [tuple(seq[b : b + step]) for b in range(0, len(seq), step)]


def get_by_path(
    obj: Mapping | Sequence | Any,
    path_: str,
    default: T | None = None,
    separator: str = ".",
) -> T | Any:
    path = []
    for item in path_.split(separator):
        if "[" not in item:
            path.append(item)
            continue
        _st, _en = item.index("["), item.index("]")
        new = item[_st + 1 : _en]
        if len(new) == len(item) - 2:
            path.append(new)
            continue
        item = item.replace("[" + new + "]", "")
        if _st == 0:
            path.extend((new, item))
        else:
            path.extend((item, new))

    value = obj
    for key in path:
        if isinstance(value, Mapping):
            if key not in value:
                return default
            value = value[key]
        elif isinstance(value, Sequence):
            try:
                value = value[int(key)]
            except Exception:
                return default
        else:
            return default
    return value


def call_with_allowed_args(func: Callable[..., T], *args, **kwargs) -> T:
    sig = inspect.signature(func)

    available_args = list(args)

    call_args = []
    call_kwargs = {}

    used_kwarg_keys = set()

    for name, param in sig.parameters.items():
        if name in kwargs:
            used_kwarg_keys.add(name)
            if param.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                call_args.append(kwargs[name])
            else:
                call_kwargs[name] = kwargs[name]
            continue

        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            call_args.extend(available_args)
            available_args = []
            continue

        if param.kind == inspect.Parameter.VAR_KEYWORD:
            continue

        found_index = -1

        for i, obj in enumerate(available_args):
            if param.annotation is inspect.Parameter.empty:
                found_index = i
                break

            try:
                if isinstance(obj, param.annotation):
                    found_index = i
                    break
            except TypeError:
                pass

        if found_index != -1:
            val = available_args.pop(found_index)
            if param.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                call_args.append(val)
            else:
                call_kwargs[name] = val

    has_var_kw = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )
    if has_var_kw:
        for k, v in kwargs.items():
            if k not in used_kwarg_keys:
                call_kwargs[k] = v

    return func(*call_args, **call_kwargs)


def ttl_cache(
    maxsize: int = 250,
    ttl: float = 3600,
    key_maker: Callable[[tuple[Any, ...], dict[str, Any]], Any] | None = None,
):
    cache = {}
    lock = Lock()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = key_maker(args, kwargs) if key_maker else args
            now = time.time()

            with lock:
                if key in cache:
                    result, expire_at = cache[key]
                    if now < expire_at:
                        return result
                    else:
                        del cache[key]

            result = func(*args, **kwargs)

            with lock:
                if len(cache) >= maxsize:
                    try:
                        cache.pop(next(iter(cache)))
                    except StopIteration:
                        pass
                cache[key] = (result, now + ttl)

            return result

        return wrapper

    return decorator
