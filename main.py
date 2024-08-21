import config as c
from methods import *


if __name__ == "__main__":
    # Fetch and save stock data
    stock_process = StockProcess()
    stock_process.date_graph_process()
    stock_process.send_email_with_attachment()