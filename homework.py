import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
STATUSES = {
    'reviewing':
        'Ваша работа принята к рассмотрению.',
    'approved':
        'У вас проверили работу "{name}"!\n\n' +
        'Ревьюеру всё понравилось, можно приступать к следующему уроку.',
    'rejected':
        'У вас проверили работу "{name}"!\n\n ' +
        'К сожалению в работе нашлись ошибки.',
}
STATUS_ERROR_MESSAGE = 'Неизвестный статус работы.\n{status}'
REQUEST_ERROR_MESSAGE = (
    'Невозможно получить ответ от ЯП.\n'
    '{url}\n '
    'Заголовок запроса: {headers}\n '
    'Параметры запроса: {params}\n'
    '{exception}'
)
JSON_ERROR_MESSAGE = (
    'Ответ от ЯП не соответсвует ожиданиям.\n'
    '{url}\n '
    'Заголовок запроса: {headers}\n '
    'Параметры запроса: {params}\n '
    'Ошибка: {error}\n'
)
BOT_ERROR_MESSAGE = 'Бот столкнулся с ошибкой:\n {error}'
BOT_START_MESSAGE = 'Бот запущен.'
BOT_SEND_MESSAGE = 'Отправлено сообщение:\n {message}'
KEY_WORDS = ['error', 'code']


def parse_homework_status(homework):
    status = homework['status']
    if status not in STATUSES:
        raise ValueError(STATUS_ERROR_MESSAGE.format(status=status))
    return STATUSES[status].format(name=homework['homework_name'])


def get_homework_statuses(current_timestamp):
    request_data = {
        'url': URL,
        'params': {'from_date': current_timestamp},
        'headers': HEADERS
    }
    try:
        response = requests.get(**request_data)
    except requests.RequestException as exception:
        raise ConnectionError(
            REQUEST_ERROR_MESSAGE.format(exception=exception, **request_data)
        )
    answer = response.json()
    for word in KEY_WORDS:
        if word in answer:
            error = answer[word]
            raise KeyError(
                JSON_ERROR_MESSAGE.format(error=error, **request_data)
            )
    return answer


def send_message(message, bot_client):
    logging.info(BOT_SEND_MESSAGE.format(message=message))
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logging.debug(BOT_START_MESSAGE)
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client,
                )
            current_timestamp = (
                new_homework.get('current_date', current_timestamp)
            )
            time.sleep(300)

        except Exception as error:
            logging.error(BOT_ERROR_MESSAGE.format(error=error))
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        handlers=[logging.FileHandler(__file__ + '.log', 'w', 'utf-8')],
        level=logging.INFO,
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
    )
    main()
