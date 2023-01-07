import logging
import os
from pathlib import Path
import time

import telegram
import requests
from dotenv import load_dotenv

load_dotenv()


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


CONNECTION_ERROR = '{error}, {url}, {headers}, {params}'
SERVICE_REJECTION = '{code}'
WRONG_ENDPOINT = '{response_status}, {url}, {headers}, {params}'
WRONG_HOMEWORK_STATUS = '{homework_status}'
WRONG_DATA_TYPE = 'Неверный тип данных {type}, вместо "dict"'
WRONG_DATA_TYPE_LIST = 'Неверный тип данных {type}, вместо "list"'
STATUS_IS_CHANGED = '{verdict}, {homework}'
STATUS_IS_NOT_CHANGED = 'Статус не изменился, нет записей'
FAILURE_TO_SEND_MESSAGE = '{error}, {message}'
GLOBAL_VARIABLE_IS_MISSING = 'Отсутствует глобальная переменная'
GLOBAL_VARIABLE_IS_EMPTY = 'Пустая глобальная переменная'
MESSAGE_IS_SENT = 'Сообщение {message} отправлено'
FORMAT_NOT_JSON = 'Формат не json {error}'
LIST_IS_EMPTY = 'Список пустой'
NO_HOMEWORK_NAME_KEY = 'В ответе API домашки отсутсвует ключ _homework_name_'
NO_HOMEWORKS_KEY = ' В ответе API домашки отсутствует ключ _homeworks'

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения пользователю в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logging.error('Ошибка отправки сообщения')
        raise MessageSendingError(FAILURE_TO_SEND_MESSAGE.format(
            error=error,
            message=message,
        ))
    logging.debug(f'Message "{message}" is sent')


def get_api_answer(current_timestamp):
    """Отправка запроса к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    all_params = dict(url=ENDPOINT, headers=HEADERS, params=params)
    try:
        response = requests.get(**all_params)
    except requests.exceptions.RequestException as error:
        raise telegram.TelegramError(CONNECTION_ERROR.format(
            error=error,
            **all_params,
        ))
    response_status = response.status_code
    if response_status != 200:
        raise EndpointError(WRONG_ENDPOINT.format(
            response_status=response_status,
            **all_params,
        ))
    try:
        return response.json()
    except Exception as error:
        raise ResponseFormatError(FORMAT_NOT_JSON.format(error))


def check_response(response):
    """Возврат статуса домашней работы."""
    if 'code' in response:
        raise ServiceError(SERVICE_REJECTION.format(
            code=response.get('code'),
        ))
    if response['homeworks']:
        return response['homeworks'][0]

    if 'homeworks' not in response.keys():
        raise ResponseContentError(NO_HOMEWORKS_KEY)

    if not isinstance(response.get('homework'), list):
        raise TypeError(WRONG_DATA_TYPE_LIST)

    else:
        raise IndexError(LIST_IS_EMPTY)


def parse_status(homework):
    """Проверка статуса ответа API."""
    if not isinstance(homework, dict):
        raise DataTypeError(WRONG_DATA_TYPE.format(type(homework)))
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_VERDICTS:
        raise NameError(WRONG_HOMEWORK_STATUS.format(homework_status))

    if homework_name is None:
        raise ResponseContentError(NO_HOMEWORK_NAME_KEY.format(homework_name))

    verdict = HOMEWORK_VERDICTS[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    for key in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ENDPOINT):
        if key is None:
            logging.critical(GLOBAL_VARIABLE_IS_MISSING)
            return False
        if not key:
            logging.critical(GLOBAL_VARIABLE_IS_EMPTY)
            return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise GlobalsError('Ошибка глобальной переменной.См. логи')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            logging.info(homework)
            current_timestamp = response.get('current_date')
        except IndexError:
            message = 'Статус работы не изменился'
            send_message(bot, message)
            logging.info(message)
        except Exception as error:
            message = f'Сбой в работе программы:{error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)
        logging.info(MESSAGE_IS_SENT.format(message))


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s, %(message)s, %(lineno)d, %(name)s',
        filemode='w',
        filename=f'{Path(__file__).stem}.log',
        level=logging.INFO,
    )
    main()
