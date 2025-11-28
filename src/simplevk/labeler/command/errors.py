class CommandError(Exception):
    """Базовый класс ошибки команды."""

    pass


class ValidationError(CommandError):
    """Ошибка валидации аргумента."""

    def __init__(self, value: str | None, reason: str):
        self.value = value
        self.reason = reason
        super().__init__(
            f"Некорректное значение {repr(value) or '<пусто>'} для аргумента: {reason}"
        )


class ExecutionError(CommandError):
    """Ошибка во время выполнения команды."""

    pass
