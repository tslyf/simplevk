import copy
import inspect
from enum import Enum
from types import UnionType
from typing import Annotated, Any, Callable, Literal, Union, get_args, get_origin

from simplevk.events import BaseEvent

from .args import (
    BOOLEAN_CHOICES,
    Arg,
    ChoiceArg,
    NumberArg,
    ParamInfo,
    ParamStub,
    StringArg,
)

_TYPE_MAP: dict[type, Arg] = {
    int: NumberArg(),
    float: NumberArg(is_float=True),
    str: StringArg(),
    bool: ChoiceArg(choices=BOOLEAN_CHOICES),
    inspect.Signature.empty: StringArg(),
}


def _unwrap_optional(annotation: Any) -> tuple[Any, bool]:
    origin = get_origin(annotation)
    if origin is UnionType or origin is Union:
        args = get_args(annotation)
        if type(None) in args:
            for arg in args:
                if arg is not type(None):
                    return arg, True
    return annotation, False


def _extract_arg_from_annotated(annotation: Any) -> tuple[Any, Arg | None, str | None]:
    if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        real_type = args[0]
        found_arg: Arg | None = None
        found_desc: str | None = None

        for meta in args[1:]:
            if isinstance(meta, Arg):
                found_arg = copy.copy(meta)
            elif isinstance(meta, type) and issubclass(meta, Arg):
                found_arg = meta()
            elif isinstance(meta, str):
                found_desc = meta

        return real_type, found_arg, found_desc

    return annotation, None, None


def _resolve_annotation_to_arg(annotation: type, strict: bool) -> Arg | None:
    if annotation in _TYPE_MAP:
        return _TYPE_MAP[annotation]

    if get_origin(annotation) is Literal:
        return ChoiceArg(choices=list(get_args(annotation)))

    elif isinstance(annotation, type) and issubclass(annotation, Enum):
        return ChoiceArg(choices=annotation)

    if strict:
        raise ValueError(f"Annotation {annotation} is not supported")

    return None


def parse_signature(func: Callable, strict: bool = False) -> list[ParamInfo]:
    arg_list: list[ParamInfo] = []
    sig = inspect.signature(func)

    for name, param in sig.parameters.items():
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        annotation, is_optional = _unwrap_optional(param.annotation)
        annotation, arg_from_annotated, description = _extract_arg_from_annotated(
            annotation
        )
        annotation, is_optional_2 = _unwrap_optional(annotation)
        is_optional |= is_optional_2

        if isinstance(annotation, type) and issubclass(annotation, BaseEvent):
            continue

        default_val = (
            param.default if param.default is not inspect.Signature.empty else ...
        )

        arg_from_param: Arg | None = None
        if isinstance(default_val, ParamStub):
            _arg = default_val.arg
            description = default_val.description or description
            default_val = default_val.default
            if isinstance(_arg, type) and issubclass(_arg, Arg):
                arg_from_param = _arg()
            elif _arg is not None:
                arg_from_param = copy.copy(_arg)

        if (
            arg_from_param is None
            and arg_from_annotated is None
            and (strict or isinstance(param.default, ParamStub))
        ):
            arg_from_param = _resolve_annotation_to_arg(annotation, strict)

        arg = arg_from_param or arg_from_annotated
        is_optional |= default_val is not ...

        if arg is None:
            continue

        if is_optional and default_val is ...:
            default_val = None

        arg_list.append(ParamInfo(arg, name, default_val, description))

    return arg_list
