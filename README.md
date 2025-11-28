# simplevk

Простая библиотека для разработки ботов ВКонтакте.
Архитектура построена на базе `dataclasses` и современных возможностях Python 3.10+, предлагая удобный интерфейс декораторов и строгую типизацию аргументов.

## Особенности

  * **Type-Safe Parsing**: Аргументы команд парсятся и валидируются согласно аннотациям типов (`int`, `bool`, `Enum`, `Literal`).
  * **Гибкая маршрутизация**: Поддержка команд, регулярных выражений, Payload и событий кнопок.
  * **Middleware**: Полноценная поддержка промежуточного ПО для разных типов событий.
  * **No Bloat**: Минимум зависимостей, фокус на скорости и чистоте API.

## Установка

```bash
pip install simplevk
```

Или через `uv`:

```bash
uv add simplevk
```

## Быстрый старт

```python
from simplevk import Bot, Message

# group_id указывать желательно, чтобы избежать лишнего запроса к API при старте
bot = Bot("YOUR_TOKEN", group_id=123456789)

# Принимать event необязательно, если он не используется
# Команды (on.command) поддерживают return строки для быстрой отправки ответа
@bot.on.command(name="ping")
def ping():
    return "Pong!"

if __name__ == "__main__":
    # Запуск LongPoll
    bot.start_listen()
```

## Система команд

Система команд в `simplevk` автоматически преобразует текст сообщения в аргументы функции.

### Базовые типы

Поддерживаются специальные типы из `simplevk`:

  * `Integer` / `Float` / `PositiveInteger` ...
  * `Word`: Одно слово **или** фраза в кавычках (например, `"аргумент с пробелом"`).
  * `Text`: Весь оставшийся текст сообщения (Greedy).
  * `Boolean`: `True` (да, +, 1, on) / `False` (нет, -, 0, off).
  * `UserID`, `GroupID`, `PeerID`: Разрешают упоминания, ссылки, ID, ответ или пересланное сообщение.

```python
from simplevk import Integer, Word, Text, Boolean, UserID

# Пример: /ban "нарушение правил" 7 да [ответом на сообщение]
@bot.on.command(name="ban")
def ban_handler(
    user: UserID,          # Спарсит ID из ответа
    reason: Word,          # Возьмет текст в кавычках как одну строку
    days: Integer,         # Спарсит int
    is_silent: Boolean = False,  # Флаг
):
    # Логика бана...
    if not is_silent:
        return f"Пользователь {user} забанен на {days} дней. Причина: {reason}"
```

### Strict Mode и Param

По умолчанию `strict=False`. Это означает, что парсер обрабатывает только известные ему типы (`Integer`, `Word` и т.д.), а остальные аргументы игнорирует (ожидая, что их передадут через Middleware).

Чтобы использовать стандартные типы Python (`int`, `str`), `Literal` или `Enum`, есть два пути:

1.  **Включить `strict=True`** (все аргументы функции считаются аргументами команды).
2.  **Использовать `Param`** (явное указание парсеру).

```python
from typing import Literal
from simplevk.labeler.command.args import Param

# Способ 1: Strict Mode
@bot.on.command(name="calc", strict=True)
def calc(a: int, op: Literal["+", "-", "*"], b: int):
    if op == "+": return str(a + b)
    # ...

# Способ 2: Param (работает при strict=False)
# Удобно, если в функцию также передаются данные из Middleware (например, user_db)
@bot.on.command(name="set status")
def set_status(
    status: Literal["online", "offline"] = Param(), 
    user_db: dict,  # Этот аргумент пропустится парсером команд
):
    return f"Статус обновлен: {status}"
```

### Catch-All команды (`name=...`)

Если передать `...` (Ellipsis) вместо имени, хендлер будет перехватывать **все** команды, которые прошли проверку префикса и всех аргументов, но не подошли под другие хендлеры.

```python
@bot.on.command(name=..., strict=True)
def wrapper(integer: int):
    # Обработка любого текста, являющегося целым числом
    return f"Integer: {integer}"
```

> **Важно про Regex**: Имя команды преобразуется в регулярное выражение. Если имя содержит спецсимволы (`.`, `?`, `*`), их необходимо экранировать вручную, иначе они будут интерпретированы как часть regex.

## Обработка ошибок валидации

По умолчанию при ошибке ввода аргументов бот отправляет сообщение с описанием ошибки. Это поведение можно переопределить.

```python
from simplevk.labeler.command.errors import ValidationError

def my_error_handler(message, error: ValidationError, handler, param):
    message.answer(
        f"Ой! Ошибка в аргументе '{param.name}': {error.reason}\n"
        f"Вы ввели: {error.value}"
    )

bot.on.command.validation_error_handler = my_error_handler
```

## Настройка префиксов

Префиксы определяются через фабрику. Вы также можете использовать стандартный regex для упоминания бота, доступный в `bot.on.command.bot_mention`.

```python
def my_prefixes(message, middlewares_data):
    # Команды работают без префикса в ЛС, но требуют /, ! или упоминание в беседах
    if not message.from_chat:
        return [""] 
    
    return ["/", "!", bot.on.command.bot_mention]

bot.on.command.prefixes_factory = my_prefixes
```

## Клавиатуры и Кнопки

Генерация JSON клавиатур и обработка нажатий (`MessageEvent`).

```python
from simplevk import Keyboard, ButtonColor, MessageEvent

# Генерация клавиатуры
kb = (
    Keyboard(inline=True)
    .add_callback("Лайк", payload={"cmd": "like"}, color=ButtonColor.POSITIVE)
    .row()
    .add_openlink("https://vk.com", "ВК")
)

# Обратите внимание: on.message и on.message_event хендлеры НЕ поддерживают return строки
@bot.on.command(name="menu")
def show_menu(event: Message):
    event.answer("Меню:", keyboard=kb)

# Обработка Callback-кнопки
@bot.on.message_event(payload={"cmd": "like"})
def like_handler(event: MessageEvent):
    event.show_snackbar("Вы поставили лайк!")
    # event.edit(...) / event.open_link(...)
```

## Middleware

Middleware позволяет выполнять код до (`pre`) и после (`post`) выполнения хендлера.
**Важно**: Списки middleware разделены для сообщений, команд и событий.

  * `bot.on.message` — для простого текста/regex/payload.
  * `bot.on.command` — для обработчиков команд.
  * `bot.on.message_event` — для кнопок.

```python
from simplevk.middlewares import BaseMiddleware

@bot.on.message.register_middleware
@bot.on.command.register_middleware
class AdminMiddleware(BaseMiddleware):
    # Метод pre может возвращать dict, который попадет в аргументы хендлера
    # Если pre вернет False, выполнение прекратится
    def pre(self, event):
        if event.from_id not in [1, 2, 3]:
            event.answer("Доступ запрещен")
            return False
        return {"is_admin": True}

    # Метод post обязателен к реализации
    def post(self, event):
        pass

@bot.on.command(name="admin_panel")
def admin_panel(event: Message, is_admin: bool):
    return "Добро пожаловать, админ."
```

## События (Events)

Помимо сообщений, библиотека поддерживает обработку других событий через `simplevk.events`:

  * `GroupJoin` / `GroupLeave`
  * `UserBlock` / `UserUnblock`

```python
from simplevk import GroupJoin

@bot.on.group_join()
def on_join(event: GroupJoin):
    print(f"Пользователь {event.user_id} вступил в группу")
```

## Планы

  * [ ] **FSM**: Машина состояний для реализации сценарных диалогов.
  * [ ] **Command-like Payload**: Внедрение парсера аргументов (как в командах) для Payload-событий.
  * [ ] Переход на асинхронный движок (asyncio).

## License

MIT