import logging
from datetime import datetime

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

from core.config import BUY_LIMIT_PERCENT, TRADING_EQUITY_RATE, SELL_LIMIT_PERCENT, TAKE_PROFIT_PERCENT, \
    STOP_LOSS_PERCENT, TESTING
from core.notifications import send_notification
from core.utils import truncate, OrderSide, handle_transaction_error, handle_transaction_info

logger = logging.getLogger()


def get_current_price(client, symbol):
    prices = client.get_all_tickers()
    x = [obj for obj in prices if symbol == obj["symbol"]]
    return x[0]


def get_recent_prices(client, symbol, interval):
    candles = client.get_klines(symbol=symbol, interval=interval)
    prices = [float(candle[4]) for candle in candles]
    return prices


def get_prices_with_time_details(client, symbol, interval, candle_array_length):
    candles = client.get_klines(symbol=symbol, interval=interval)
    prices = [
        {
            "open_time": datetime.fromtimestamp(candle[0] / 1000),
            "close_time": datetime.fromtimestamp(candle[6] / 1000),
            "open": float(candle[1]),
            "close": float(candle[4])
        }
        for candle in candles[-candle_array_length:]
    ]
    return prices


def get_last_trade(client, symbol):
    trade = client.get_my_trades(symbol=symbol)[-1]
    last_trade_info = {
        "symbol": trade["symbol"],
        "price": trade["price"],
        "qty": trade["qty"],
        "quoteQty": trade["quoteQty"],
        "commission": trade["commission"],
        "commissionAsset": trade["commissionAsset"],
        "quoteCommissionQty": float(trade["commission"]) * float(trade["price"]),
        "time": datetime.fromtimestamp(int(trade["time"]) / 1000),
        "isBuyer": trade["isBuyer"]
    }
    return last_trade_info


def is_open_position(client, symbol):
    last_trade = get_last_trade(client, symbol)
    return last_trade["isBuyer"]


def get_balance(client, symbol='USDT'):
    balance = client.get_asset_balance(asset=symbol)["free"]
    return balance


def limit_buy_order(client, base_asset, quote_asset):
    current_price = float(get_current_price(client, base_asset + quote_asset)["price"])
    fiat_balance = float(get_balance(client, quote_asset))

    limit_price = round(current_price * BUY_LIMIT_PERCENT, 2)
    fiat_buying_value = round(fiat_balance * TRADING_EQUITY_RATE, 4)
    base_asset_quantity = round(fiat_buying_value / current_price, 4)

    logger.info(f"{quote_asset} balance: {fiat_balance}")
    logger.info(f"Current {base_asset} price: {current_price} {quote_asset}, limit price: {limit_price}")
    logger.info(f"Buying: {base_asset_quantity} {base_asset} for {fiat_buying_value} {quote_asset}")

    if not TESTING:
        order = client.create_order(
            symbol=base_asset + quote_asset,
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_LIMIT,
            timeInForce=Client.TIME_IN_FORCE_GTC,
            quantity=base_asset_quantity,
            price=limit_price)

        logger.info(f"Order info: {order}")


def limit_sell_order(client, base_asset, quote_asset):
    current_price = float(get_current_price(client, base_asset + quote_asset)["price"])
    balance = float(get_balance(client, base_asset))
    balance_value = round(balance * current_price, 5)

    limit_price = round(current_price * SELL_LIMIT_PERCENT, 2)
    base_asset_sell_quantity = truncate(balance, 5)
    transaction_value = base_asset_sell_quantity * current_price

    logger.info(f"{base_asset} balance:{balance}, balance value: {balance_value} {quote_asset}")
    logger.info(f"Current {base_asset} price: {current_price} {quote_asset}, limit price: {limit_price} {quote_asset}")
    logger.info(f"Selling {base_asset_sell_quantity} {base_asset} for {transaction_value} {quote_asset}")

    if not TESTING:
        order = client.create_order(
            symbol=base_asset + quote_asset,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_LIMIT,
            timeInForce=Client.TIME_IN_FORCE_GTC,
            quantity=base_asset_sell_quantity,
            price=limit_price)

        print(f"Order info: {order}")


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


def send_order(client, side, closing_price, base_currency, quote_currency):
    if side == OrderSide.buy:
        try:
            limit_buy_order(client, base_currency, quote_currency)
        except (BinanceAPIException, BinanceOrderException) as e:
            handle_transaction_error(e)
        except Exception as e:
            handle_transaction_error(e)
        handle_transaction_info(OrderSide.buy, base_currency, closing_price, quote_currency)
    elif side == OrderSide.sell:
        try:
            limit_sell_order(client, base_currency, quote_currency)
        except (BinanceAPIException, BinanceOrderException) as e:
            handle_transaction_error(e)
        except Exception as e:
            handle_transaction_error(e)
        handle_transaction_info(OrderSide.sell, base_currency, closing_price, quote_currency)