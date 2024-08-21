
from methods import *


if __name__ == "__main__":
    # Fetch and save stock data
    stock_process = StockProcess(c.STOCKS_ETF)
    stock_process.date_graph_process()
    stock_process.send_email_with_attachment()