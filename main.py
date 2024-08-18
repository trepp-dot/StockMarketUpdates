
from methods import *


if __name__ == "__main__":
    for stock, desc in c.STOCKS_ETF.items():
        stock_data = fetch_stock_data(symbol=stock, use_local_data=True)
        generate_graph(stock, desc,  stock_data)

    send_email_with_attachment()