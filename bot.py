import logging

import websocket
from binance.client import Client

from core.indicators import get_moving_averages
from core.config import API_KEY, SECRET_KEY
from core.utils import configure_logger, process_msg, OrderSide, \
    calculate_trading_signal
from core.trading import get_recent_prices, send_order

BASE_CURRENCY = "BTC"
QUOTE_CURRENCY = "EUR"
TRADE_SYMBOL = BASE_CURRENCY + QUOTE_CURRENCY
INTERVAL = Client.KLINE_INTERVAL_1MINUTE
SOCKET = f"wss://stream.binance.com:9443/ws/{TRADE_SYMBOL.lower()}@kline_{INTERVAL}"
MA_WINDOW_SIZE = 7


def on_open(ws_app):
    logger.info("Connection opened")


def on_close(ws_app, close_status_code, close_msg):
    logger.info(f"Connection closed")


def on_message(ws_app, ws_message):
    global binance_client, closing_prices, in_position

    closing_price = process_msg(ws_message)

    if not closing_price or len(closing_prices) < MA_WINDOW_SIZE:
        return

    logger.info(f"Closing price received: {closing_price}")
    closing_prices.append(closing_price)

    moving_averages = get_moving_averages(closing_prices, MA_WINDOW_SIZE)
    trading_signal = calculate_trading_signal(closing_prices, moving_averages)

    if trading_signal == OrderSide.buy:
        if not in_position:
            logger.info("Sending buy order")
            send_order(binance_client, OrderSide.buy, closing_price, BASE_CURRENCY, QUOTE_CURRENCY)
            in_position = True
    elif trading_signal == OrderSide.sell:
        if in_position:
            logger.info("Sending sell order")
            send_order(binance_client, OrderSide.sell, closing_price, BASE_CURRENCY, QUOTE_CURRENCY)
            in_position = False


if __name__ == '__main__':
    configure_logger("logs")
    logger = logging.getLogger()

    binance_client = Client(API_KEY, SECRET_KEY)

    closing_prices = get_recent_prices(binance_client, TRADE_SYMBOL, INTERVAL)
    in_position = False

    logger.info("Running started")
    binance_ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    binance_ws.run_forever()
