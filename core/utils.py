import enum
import json
import logging
import os
from core.notifications import send_notification


class OrderSide(enum.Enum):
    buy = 1
    sell = 2


def handle_transaction_error(logger, error):
    error_message = f"An error occured when trying to send order: {error}"
    logger.info(error_message)
    send_notification(error_message)


def handle_transaction_info(logger, order_type, base_currency, price, quote_currency):
    if order_type == OrderSide.buy:
        transaction_message = f"Bought {base_currency} at (approximately) {price} {quote_currency}"
    if order_type == OrderSide.sell:
        transaction_message = f"Sold {base_currency} at (approximately) {price} {quote_currency}"
    logger.info(transaction_message)
    send_notification(transaction_message)


def print_symbol_info(client, symbol):
    info = client.get_symbol_info(symbol)
    print(json.dumps(info, indent=4))


def get_non_zero_balances(client):
    info = client.get_account()
    balances = info["balances"]
    assets = [obj for obj in balances if float(obj["free"]) > 0]
    return assets


def check_directory_existence(dir_name):
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)


def configure_logger(logging_directory):
    check_directory_existence(logging_directory)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler("logs/bot.log")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)


def process_msg(message):
    json_message = json.loads(message)
    candle_data = json_message['k']

    is_candle_closed = candle_data['x']
    closing_price = float(candle_data['c'])

    return is_candle_closed, closing_price


def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier