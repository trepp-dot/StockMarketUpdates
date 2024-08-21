import base64
import os
import pandas as pd
import matplotlib.pyplot as plt
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta
import matplotlib.dates as mdates

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

import config as c

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')


class StockProcess:
    def __init__(self):
        self.symbols_dict = c.STOCKS_ETF
        self.data = pd.DataFrame()
        self.symbol = None
        self.output_path = os.path.join('output', "{}.png")

# Fetch stock data
    def date_graph_process(self):
        for symbol, desc in self.symbols_dict.items():
            self.symbol = symbol
            self.data = self.fetch_stock_data(use_local_data=False)
            self.generate_graph(desc)

    def fetch_stock_data(self, use_local_data=False):
        if use_local_data:
            if os.path.exists(f"data/{self.symbol}.csv"):
                data = pd.read_csv(f"data/{self.symbol}.csv", index_col=0)
                return data
            else:
                print(f"Local data not found for {self.symbol}")
                ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
                data, meta_data = ts.get_daily(symbol=self.symbol, outputsize='compact')
                # save to CSV
                data.to_csv(f"data/{self.symbol}.csv")
        else:
            ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
            data, meta_data = ts.get_daily(symbol=self.symbol, outputsize='compact')
        return data

    # Generate graph for each stock
    def generate_graph(self, desc):
        data = self.data.sort_index()
        # Calculate yield since purchase
        purchase_price, yield_since_purchase, yearly_yield, purchase_date = None, None, None, None

        # Set up the figure and subplots
        fig, axs = plt.subplots(2, 1, figsize=(10, 10))
        # Full-period graph
        axs[0].plot(data['4. close'], label="Full Period")
        axs[0].set_title(f"{desc} Stock Price (Full Period)")
        axs[0].set_xlabel('Date')
        axs[0].set_ylabel('Price')
        if self.symbol in c.ANNOTATIONS:
            purchase_price, yield_since_purchase, yearly_yield, purchase_date = self.calc_yield_since_purchase(data)
            axs[0].annotate(c.ANNOTATIONS[self.symbol], xy=(data.index[-20], data['4. close'][-20]),
                            xytext=(data.index[-60], data['4. close'][-40]),
                            arrowprops=dict(facecolor='black', shrink=0.05))
            axs[0].axhline(y=purchase_price, color='r', linestyle='--', label=f"Bought at {purchase_price} on {purchase_date}")
        axs[0].legend()

        axs[0].xaxis.set_major_locator(mdates.MonthLocator())  # Set major ticks to months
        # axs[0].xaxis.set_major_formatter(mdates.DateFormatter('%b'))  # Format ticks as month abbreviations (e.g., Jan, Feb)

        # 3-month period graph
        three_months_ago = datetime.now() - timedelta(days=90)
        three_month_data = data[data.index >= three_months_ago.strftime('%Y-%m-%d')]
        if not three_month_data.empty:
            axs[1].plot(three_month_data['4. close'], label="Last 3 Months")
            axs[1].set_title(f"{self.symbol} Stock Price (Last 3 Months)")
            axs[1].set_xlabel('Date')
            axs[1].set_ylabel('Price')
            if purchase_price:
                axs[1].axhline(y=purchase_price, color='r', linestyle='--', label=f"Bought at {purchase_price} on {purchase_date}")
            axs[1].legend()

            axs[1].xaxis.set_major_locator(mdates.MonthLocator())  # Set major ticks to months
            # axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%b'))  # Format ticks as month abbreviations (e.g., Jan, Feb)

        # Add yield information as text
        if yield_since_purchase:
            fig.text(0.5, 0.01, f"Yield since purchase: {yield_since_purchase}%  |  Yearly yield: {yearly_yield}%", ha="center", fontsize=12)

        plt.tight_layout(rect=[0.0, 0.03, 1.0, 0.95])
        os.makedirs(os.path.dirname(self.output_path.format(self.symbol)), exist_ok=True)
        plt.savefig(self.output_path.format(self.symbol))
        # plt.savefig(f"graph/{self.symbol}.png")
        plt.close()

    def calc_yield_since_purchase(self, data):
        purchase_date = c.ANNOTATIONS[self.symbol].split(' on ')[-1]
        purchase_price = self.get_price_on_date(data, purchase_date)
        current_price = self.data['4. close'].iloc[-1]
        yield_since_purchase = self.calculate_yield(purchase_price, current_price) if purchase_price else None

        # Calculate yearly yield
        one_year_ago = datetime.now() - timedelta(days=365)
        one_year_data = self.data[self.data.index >= one_year_ago.strftime('%Y-%m-%d')]
        if not one_year_data.empty:
            price_one_year_ago = one_year_data['4. close'].iloc[0]
            yearly_yield = self.calculate_yield(price_one_year_ago, current_price)
        else:
            yearly_yield = None
        return purchase_price, yield_since_purchase, yearly_yield, purchase_date

    @staticmethod
    def get_price_on_date(data, date_str):
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            price_on_date = data.loc[date.strftime('%Y-%m-%d')]['4. close']
            return price_on_date
        except KeyError:
            print(f"No data available for {date_str}")
            return None

    @staticmethod
    def calculate_yield(purchase_price, current_price):
        return round(((current_price - purchase_price) / purchase_price) * 100, 2)

    # Send email with stock updates
    def send_email_with_attachment(self):
        message = Mail(
            from_email=EMAIL_ADDRESS,
            to_emails=RECIPIENT_EMAIL,
            subject='Daily Stock Market Update',
            plain_text_content='Please find the daily stock market update attached.'
        )

        # Attach images
        for symbol in self.symbols_dict:  # List of stocks
            with open(self.output_path.format(symbol), "rb") as f:
                data = f.read()
                encoded = base64.b64encode(data).decode()
                attachment = Attachment(
                    FileContent(encoded),
                    FileName(f"{symbol}.png"),
                    FileType('image/png'),
                    Disposition('attachment')
                )
                message.add_attachment(attachment)

        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(f"Email sent with status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending email: {str(e)}")
