from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

from core.config import BUY_LIMIT_PERCENT, TRADING_EQUITY_RATE, SELL_LIMIT_PERCENT, TAKE_PROFIT_PERCENT, \
    STOP_LOSS_PERCENT
from core.notifications import send_notification


def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


def get_current_price(client, symbol):
    prices = client.get_all_tickers()
    x = [obj for obj in prices if symbol == obj["symbol"]]
    return x[0]


def get_recent_prices(client, symbol, interval):
    candles = client.get_klines(symbol=symbol, interval=interval)
    prices = [float(candle[4]) for candle in candles]
    return prices


def get_balance(client, symbol='USDT'):
    balance = client.get_asset_balance(asset=symbol)["free"]
    return balance


def limit_buy_order(client, base_asset, quote_asset):
    current_price = float(get_current_price(client, base_asset + quote_asset)["price"])
    fiat_balance = float(get_balance(client, quote_asset))
    print(f"{quote_asset} balance:{fiat_balance}")

    limit_price = round(current_price * BUY_LIMIT_PERCENT, 2)
    fiat_buying_value = round(fiat_balance * TRADING_EQUITY_RATE, 4)
    base_asset_quantity = round(fiat_buying_value / current_price, 4)

    print(f"Current {base_asset} price: {current_price} {quote_asset}, buying with: {fiat_buying_value} {quote_asset}")
    print(f"Limit price: {limit_price} {quote_asset}, buying: {base_asset_quantity} {base_asset}")

    order = client.create_order(
        symbol=base_asset + quote_asset,
        side=Client.SIDE_BUY,
        type=Client.ORDER_TYPE_LIMIT,
        timeInForce=Client.TIME_IN_FORCE_GTC,
        quantity=base_asset_quantity,
        price=limit_price)


def limit_sell_order(client, base_asset, quote_asset):
    current_price = float(get_current_price(client, base_asset + quote_asset)["price"])
    balance = float(get_balance(client, base_asset))
    print(f"{base_asset} balance:{balance}")

    limit_price = round(current_price * SELL_LIMIT_PERCENT, 2)
    balance_value = round(balance * current_price, 5)
    base_asset_sell_quantity = truncate(balance, 5)

    print(f"Current price: {current_price} {quote_asset}, balance value: {balance_value} {quote_asset}")
    print(f"Limit price: {limit_price} {quote_asset}")
    print(
        f"Selling {base_asset_sell_quantity} {base_asset} worth of {base_asset_sell_quantity * current_price} {quote_asset}")

    order = client.create_order(
        symbol=base_asset + quote_asset,
        side=Client.SIDE_SELL,
        type=Client.ORDER_TYPE_LIMIT,
        timeInForce=Client.TIME_IN_FORCE_GTC,
        quantity=base_asset_sell_quantity,
        price=limit_price)


def oco_sell(client, pair):
    current_price = float(get_current_price(client, pair)["price"])
    balance = float(get_balance(client, "ETH"))

    price = current_price * TAKE_PROFIT_PERCENT  # basically the take profit price
    stop_price = current_price * STOP_LOSS_PERCENT
    stop_limit_price = stop_price * SELL_LIMIT_PERCENT

    qty = round(balance * 0.99, 4)
    trade_value = current_price * qty

    print(current_price, price, stop_price, stop_limit_price, trade_value)

    try:
        order = client.create_oco_order(
            symbol=pair,
            side=Client.SIDE_SELL,
            stopLimitTimeInForce=Client.TIME_IN_FORCE_GTC,
            quantity=qty,
            price=price,
            stopPrice=stop_price,
            stopLimitPrice=stop_limit_price,
        )
    except (BinanceAPIException, BinanceOrderException) as e:
        error_message = f"An error occured when trying to send order: {e}"
        send_notification(error_message)
        print(error_message)
    except Exception as e:
        error_message = f"An error occured when trying to send order: {e}"
        send_notification(error_message)
        print(error_message)
