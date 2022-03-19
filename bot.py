import logging

import websocket
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

from core.indicators import get_moving_averages
from core.config import API_KEY, SECRET_KEY
from core.utils import handle_transaction_error, handle_transaction_info, configure_logger, process_msg, OrderSide
from core.trading import limit_buy_order, limit_sell_order, get_recent_prices, is_open_position

BASE_CURRENCY = "BTC"
QUOTE_CURRENCY = "EUR"
TRADE_SYMBOL = BASE_CURRENCY + QUOTE_CURRENCY
INTERVAL = Client.KLINE_INTERVAL_1MINUTE
SOCKET = f"wss://stream.binance.com:9443/ws/{TRADE_SYMBOL.lower()}@kline_{INTERVAL}"
MA_WINDOW_SIZE = 7


def calculate_trading_signal(prices, moving_averages):
    trading_signal = None

    last_closed_price = prices[-1]
    last_but_one_closed_price = prices[-2]

    last_ma_value = moving_averages[-1]
    last_but_one_ma_value = moving_averages[-2]

    if last_but_one_closed_price < last_but_one_ma_value and last_closed_price > last_ma_value:
        trading_signal = OrderSide.buy

    if last_but_one_closed_price > last_but_one_ma_value and last_closed_price < last_ma_value:
        trading_signal = OrderSide.sell

    return trading_signal


def send_order(client, side, closing_price, base_currency, quote_currency):
    if side == OrderSide.buy:
        try:
            limit_buy_order(client, base_currency, quote_currency)
        except (BinanceAPIException, BinanceOrderException) as e:
            handle_transaction_error(logger, e)
        except Exception as e:
            handle_transaction_error(logger, e)
        handle_transaction_info(logger, OrderSide.buy, base_currency, closing_price, quote_currency)
    elif side == OrderSide.sell:
        try:
            limit_sell_order(client, base_currency, quote_currency)
        except (BinanceAPIException, BinanceOrderException) as e:
            handle_transaction_error(logger, e)
        except Exception as e:
            handle_transaction_error(logger, e)
        handle_transaction_info(logger, OrderSide.sell, base_currency, closing_price, quote_currency)


def on_open(ws_app):
    logger.info("Connection opened")


def on_close(ws_app, close_status_code, close_msg):
    logger.info(f"Connection closed")


def on_message(ws_app, ws_message):
    global binance_client, closing_prices, in_position

    is_candle_closed, closing_price = process_msg(ws_message)

    if not is_candle_closed:
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