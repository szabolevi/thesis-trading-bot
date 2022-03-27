import time
from datetime import datetime

from binance import Client
from core.config import API_KEY, SECRET_KEY
from core.indicators import get_moving_averages
from core.trading import send_order
from core.utils import OrderSide, configure_logger

BASE_CURRENCY = "BTC"
QUOTE_CURRENCY = "EUR"
TRADE_SYMBOL = f"{BASE_CURRENCY}{QUOTE_CURRENCY}"
INTERVAL = Client.KLINE_INTERVAL_1MINUTE


def get_prices(client, symbol, interval, number_of_candles):
    candles = client.get_klines(symbol=symbol, interval=interval)
    prices = [float(candle[4]) for candle in candles[-number_of_candles:]]
    return prices


def calculate_trading_signal(prices, moving_averages):
    trading_signal = None

    last_closed_price = prices[-1]
    last_but_one_closed_price = prices[-2]

    last_ma_value = moving_averages[-1]
    last_but_one_ma_value = moving_averages[-2]

    print(datetime.now())
    print(f"Last but one closing price: {last_but_one_closed_price}, last but one MA value: {last_but_one_ma_value}")
    print(f"Last closing price: {last_closed_price}, last MA value: {last_ma_value}")

    if last_but_one_closed_price < last_but_one_ma_value and last_closed_price > last_ma_value:
        trading_signal = OrderSide.buy

    if last_but_one_closed_price > last_but_one_ma_value and last_closed_price < last_ma_value:
        trading_signal = OrderSide.sell

    return trading_signal


def trading_handler():
    print("Running started")
    in_position = False
    binance_client = Client(API_KEY, SECRET_KEY)
    window_size = 7
    number_of_candles = window_size + 2  # we throw away the last, open candle and need one more candle for the last but one ma value

    closing_prices = get_prices(binance_client, TRADE_SYMBOL, INTERVAL, number_of_candles)[:-1]
    moving_averages = get_moving_averages(closing_prices, window_size=window_size)

    trading_signal = calculate_trading_signal(closing_prices, moving_averages)
    print("Everything initialized")
    if trading_signal == OrderSide.buy:
        if not in_position:
            print("Sending buy order")
            send_order(binance_client, OrderSide.buy, closing_prices[-1], BASE_CURRENCY, QUOTE_CURRENCY)
            in_position = True
    elif trading_signal == OrderSide.sell:
        if in_position:
            print("Sending sell order")
            send_order(binance_client, OrderSide.sell, closing_prices[-1], BASE_CURRENCY, QUOTE_CURRENCY)
            in_position = False


if __name__ == '__main__':
    pass
    # in_position = False
    # while True:
    #     trading_handler()
    #     time.sleep(60)
