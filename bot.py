import json
import logging

import websocket
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

from core.indicators import get_moving_averages
from core.config import API_KEY, SECRET_KEY
from core.utils import handle_transaction_error, handle_transaction_info
from core.trading import limit_buy_order, limit_sell_order, get_recent_prices

BASE_CURRENCY = "ETH"
QUOTE_CURRENCY = "EUR"
TRADE_SYMBOL = BASE_CURRENCY + QUOTE_CURRENCY
INTERVAL = Client.KLINE_INTERVAL_1MINUTE
SOCKET = f"wss://stream.binance.com:9443/ws/{TRADE_SYMBOL.lower()}@kline_{INTERVAL}"


def on_open(ws_app):
    logger.info("Connection opened")


def on_close(ws_app, close_status_code, close_msg):
    logger.info(f"Connection closed")


def on_message(ws_app, message):
    global closing_prices, in_position

    json_message = json.loads(message)
    candle_data = json_message['k']

    is_candle_closed = candle_data['x']
    closing_price = float(candle_data['c'])

    if is_candle_closed:
        logger.info(f"Closing price received: {closing_price}")
        closing_prices.append(closing_price)

        window_size = 7
        moving_averages = get_moving_averages(closing_prices, window_size)

        last_closing_price = closing_prices[-1]
        last_but_one_closing_price = closing_prices[-2]

        last_ma_value = moving_averages[-1]
        last_but_one_ma_value = moving_averages[-2]

        if last_but_one_closing_price < last_but_one_ma_value and last_closing_price > last_ma_value:
            if not in_position:
                logger.info("Sending buy order")
                # try:
                #     limit_buy_order(binance_client, BASE_CURRENCY, QUOTE_CURRENCY)
                # except (BinanceAPIException, BinanceOrderException) as e:
                #     handle_transaction_error(logger, e)
                # except Exception as e:
                #     handle_transaction_error(logger, e)
                # handle_transaction_info(logger, "buy", BASE_CURRENCY, closing_price, BASE_CURRENCY)
                in_position = True
        if last_but_one_closing_price > last_but_one_ma_value and last_closing_price < last_ma_value:
            if in_position:
                logger.info("Sending sell order")
                # try:
                #     limit_sell_order(binance_client, BASE_CURRENCY, QUOTE_CURRENCY)
                # except (BinanceAPIException, BinanceOrderException) as e:
                #     handle_transaction_error(logger, e)
                # except Exception as e:
                #     handle_transaction_error(logger, e)
                # handle_transaction_info(logger, "sell", BASE_CURRENCY, closing_price, QUOTE_CURRENCY)
                in_position = False


if __name__ == '__main__':
    # Logging configuration
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logFormatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    fileHandler = logging.FileHandler("logs/bot.log")
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    # ---------------------------------------------------------------------------
    binance_client = Client(API_KEY, SECRET_KEY)

    print(API_KEY, SECRET_KEY)
    closing_prices = get_recent_prices(binance_client, TRADE_SYMBOL, INTERVAL)
    in_position = False

    logger.info("Running started")
    binance_ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    binance_ws.run_forever()
