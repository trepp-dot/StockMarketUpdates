import os

STOCKS = [
    '^N225',    # Nikkei 225 Index
    '^RUT',     # Russell 2000 Index
    '^MSCIWD',  # MSCI World Index (may vary by platform)
    '^NDX',     # Nasdaq 100 Index
    '^GSPC'     # S&P 500 Index
]
STOCKS_ETF = {
    'SPY': 'S&P 500',
    'EWJ': 'Nikkei 225',
    'IWM': 'Russell 2000',
    'URTH': 'MSCI World Index',
    'QQQ': 'Nasdaq 100',
}
ANNOTATIONS = {'AAPL': 'Bought on 2023-01-01', 'MSFT': 'Bought on 2023-03-15'}

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
