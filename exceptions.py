class ServiceError(Exception):
    """Ошибка отсутствия доступа по заданному эндпойнту."""

    pass


class NetworkError(Exception):
    """Ошибка отсутствия сети."""

    pass


class EndpointError(Exception):
    """Ошибка, если эндпойнт не корректен."""

    pass


class MessageSendingError(Exception):
    """Ошибка отправки сообщения."""

    pass


class GlobalsError(Exception):
    """Ошибка, если есть пустые глобальные переменные."""

    pass


class DataTypeError(Exception):
    """Ошибка, если тип данных не dict."""

    pass


class ResponseFormatError(Exception):
    """Ошибка, если формат response не json."""

    pass


class ResponseContentError(Exception):
    """Ошибка, если содежимое отклика некорректно."""

    pass