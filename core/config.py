import os
from core.envloader import load_env

load_env()

TESTING = True

API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

BUY_LIMIT_PERCENT = 1.02
TRADING_EQUITY_RATE = 0.1
SELL_LIMIT_PERCENT = 0.98
TAKE_PROFIT_PERCENT = 1.06
STOP_LOSS_PERCENT = 0.97
