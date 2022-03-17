import time
from datetime import datetime

from binance import Client
from core.config import API_KEY, SECRET_KEY
from core.indicators import get_moving_averages

BASE_CURRENCY = "BTC"
QUOTE_CURRENCY = "EUR"
TRADE_SYMBOL = f"{BASE_CURRENCY}{QUOTE_CURRENCY}"
INTERVAL = Client.KLINE_INTERVAL_3MINUTE


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

    print(datetime.now(),
          f"Last but one closing price: {last_but_one_closed_price}, last but one moving average value: {last_but_one_ma_value}")
    print(datetime.now(), f"Last closing price: {last_closed_price}, last moving average value: {last_ma_value}")

    if last_but_one_closed_price < last_but_one_ma_value and last_closed_price > last_ma_value:
        trading_signal = "BUY"

    if last_but_one_closed_price > last_but_one_ma_value and last_closed_price < last_ma_value:
        trading_signal = "SELL"

    return trading_signal


def trading_handler():
    global IN_POSITION
    client = Client(API_KEY, SECRET_KEY)
    window_size = 7
    number_of_candles = window_size + 2  # we throw away the last, open candle and need one more candle for the last but one ma value

    prices_without_open_candle = get_prices(client, TRADE_SYMBOL, INTERVAL, number_of_candles)[:-1]
    moving_averages = get_moving_averages(prices_without_open_candle, window_size=window_size)

    trading_signal = calculate_trading_signal(prices_without_open_candle, moving_averages)
    if trading_signal == "BUY":
        if not IN_POSITION:
            print("BUY")
            IN_POSITION = True
    if trading_signal == "SELL":
        if IN_POSITION:
            print("SELL")
            IN_POSITION = False


if __name__ == '__main__':
    IN_POSITION = False
    while True:
        trading_handler()
        time.sleep(60)
