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
ANSWER = 'У вас проверили работу "{}"!\n\n'
STATUSES = {
    'reviewing': 'Ваша работа принята к рассмотрению.',
    'approved':
    ANSWER + 'Ревьюеру всё понравилось, можно приступать к следующему уроку.',
    'rejected': ANSWER + 'К сожалению в работе нашлись ошибки.',
}


def parse_homework_status(homework):
    name = homework.get('homework_name')
    status = homework.get('status')
    if status not in STATUSES:
        logging.error('Ошибка ответа от ЯП.')
        return f'Неизвестный статус работы. {name}'
    verdict = STATUSES[status]
    return verdict.format(name)


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
    except requests.RequestException:
        logging.error(
            f'Невозможно получить ответ от ЯП.\n{URL}\n'
            f'Параметры запроса: {HEADERS} \n {params}'
        )
        return {}
    answer = response.json()
    if 'code' in answer.keys():
        error = answer.get('message')
        logging.error(f'Ошибка подключения к ЯП.\n {error}')
        return {}
    if answer.get('homeworks') is None:
        logging.error('Вернулся неожиданный ответ.')
        return {}
    return answer


def send_message(message, bot_client=None):
    logging.info(f'Отправлено сообщение:\n"{message}"')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logging.debug('Бот запущен.')
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client
                )
            current_timestamp = (
                new_homework.get('current_date', current_timestamp)
            )
            time.sleep(300)

        except Exception as error:
            logging.error(f'Бот столкнулся с ошибкой: {error}')
            time.sleep(5)


logging.basicConfig(
    handlers=[logging.FileHandler(__file__ + '.log', 'w', 'utf-8')],
    level=logging.INFO,
    format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
)

if __name__ == '__main__':
    main()
