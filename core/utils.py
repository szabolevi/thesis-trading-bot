import json
import sys

from core.notifications import send_notification


def handle_transaction_error(logger, error):
    error_message = f"An error occured when trying to send order: {error}"
    send_notification(error_message)
    logger.info(error_message)


def handle_transaction_info(logger, order_type, base_currency, price, quote_currency):
    if order_type == "buy":
        transaction_message = f"Bought {base_currency} at (approximately) {price} {quote_currency}"
    if order_type == "sell":
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
