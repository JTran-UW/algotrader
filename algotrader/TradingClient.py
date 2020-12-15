import requests
import json
import pandas as pd
from datetime import datetime
from lxml import html

class TradingClient:
    def __init__(self, outfile, balance):
        """
        Client for making simulated stock market trades \n
        
        :param outfile: CSV file name of portfolio
        :param balance: txt file name of balance sheet
        """
        self.portfolio_name = outfile
        self.balance_sheet_name = balance

        # Create portfolio
        try:
            self.portfolio = pd.read_csv(outfile, index_col="id")
        except FileNotFoundError:
            self.portfolio = self.create_portfolio(outfile)

        # Open balance file
        try:
            self.balance_sheet = open(balance, "r+")
            self.balance = self.balance_sheet.read()
        except FileNotFoundError:
            init_balance = 10000
            self.create_balance_sheet(balance, init_balance)
            self.balance_sheet = open(balance, "r+")
            self.balance = self.balance_sheet.read()

    def create_portfolio(self, filename):
        """
        Create a new CSV portfolio flie \n

        :param filename: name of file
        :return: pd dataframe of portfolio
        """
        init_df = pd.DataFrame({
            "id": [],
            "Ticker": [],
            "Date Purchased": [],
            "Price Purchased": [],
            "Date Last Refreshed": [],
            "Current Price": [],
            "Value Increase": []
        })
        init_df.set_index("id", inplace=True)
        init_df.to_csv(filename)

        return init_df
    
    def create_balance_sheet(self, filename, amount):
        """
        Create a new balance sheet

        :param filename: text file name to store balance
        :param amount: initial amount to store
        """
        balance_sheet = open(filename, "w+")
        balance_sheet.write(str(amount))
        balance_sheet.close()

    def get_stock_price(self, ticker):
        """
        Queries alpha vantage for ticker info, returns its price \n
        
        :param ticker: stock ticker
        :return: price of stock
        """
        price_xpath = '//*[@id="quote-header-info"]/div[3]/div[1]/div/span[1]'
        response = requests.get(f"https://finance.yahoo.com/quote/{ticker}/")
        html_res = html.fromstring(response.content)

        price = html_res.xpath(price_xpath)[0].text
        return float(price)

    def buy(self, ticker, price, quantity):
        """
        Buy stocks \n

        :param ticker: string of stock ticker \n
        :param price: price of ticker
        :param quantity: quantity of stock to buy \n
        :return: list data about stock added to portfolio
        """
        date = datetime.today()
        purchase = list()
        
        for i in range(quantity):
            id_num = self.portfolio.shape[0]
            purchase = [ticker, date, price, date, price, 0.0]
            self.portfolio.loc[id_num] = purchase

            self.update_balance(-1 * price)

        self.save()
        return purchase
    
    def refresh(self, price_db):
        """
        Refresh info in portfolio \n
        
        :param price_db: portfolio containing keys of all stocks, values of their prices
        :return: full portfolio with changes
        """
        for id_num, row in self.portfolio.iterrows():
            # Refresh all "current" variables
            current_price = price_db[row["Ticker"]]

            self.portfolio.at[id_num, "Date Last Refreshed"] = datetime.today()
            self.portfolio.at[id_num, "Current Price"] = current_price

            current_price = float(self.portfolio.at[id_num, "Current Price"])
            price_purchased = float(self.portfolio.at[id_num, "Price Purchased"])
            change = current_price - price_purchased
            self.portfolio.at[id_num, "Value Increase"] = round(change, 2)
            self.update_balance(change)

        self.save()
        return self.portfolio

    def stock_summary(self, ticker):
        """
        Return a summary of major indicators for a single stock \n

        :param ticker: stock to be summarized \n
        :return: dictionary of summary
        """
        # Summary indicators
        summary = {
            "Total Value Purchased": 0,
            "Total Quantity Purchased": 0,
            "Total Value Owned": 0,
            "Total Quantity Owned": 0,
            "Total Value Increase": 0
        }

        for id_num, row in self.portfolio.iterrows():
            if row["Ticker"] == ticker:
                summary["Total Value Purchased"] += row["Price Purchased"]
                summary["Total Quantity Purchased"] += 1
                summary["Total Value Owned"] += row["Current Price"]
                summary["Total Quantity Owned"] += 1
                summary["Total Value Increase"] += row["Value Increase"]

        summary["Total Value Increase %"] = 100 * (summary["Total Value Owned"] / summary["Total Value Purchased"]) - 100
        return summary
    
    def portfolio_summary(self):
        """
        Get a summary of how your portfolio is doing

        :return: dictionary of leading portfolio indicators
        """
        best = self.portfolio.sort_values(by=["Value Increase"], ascending=False)
        best = best.iloc[[0]].to_dict("records")[0]
        worst = self.portfolio.sort_values(by=["Value Increase"], ascending=True).iloc[[0]]
        worst = worst.iloc[[0]].to_dict("records")[0]
        
        owned = sum(self.portfolio["Current Price"])
        paid = sum(self.portfolio["Price Purchased"])

        summary = {
            "Best Performing Stock": {
                "Ticker": best["Ticker"],
                "Buy Price": best["Price Purchased"],
                "Current Price": best["Current Price"],
                "Change": best["Value Increase"],
                "% Change": 100 * (best["Current Price"] / best["Price Purchased"]) - 100,
            },
            "Worst Performing Stock": {
                "Ticker": worst["Ticker"],
                "Buy Price": worst["Price Purchased"],
                "Current Price": worst["Current Price"],
                "Change": worst["Value Increase"],
                "% Change": 100 * (worst["Current Price"] / worst["Price Purchased"]) - 100,
            },
            "Total Change": owned - paid,
            "Total % Change": 100 * (owned / paid) - 100
        }

        return summary

    def sell(self, ticker, quantity):
        """
        Sell a stock \n

        :param ticker: stock ticker to be sold \n
        :param quantity: quantity of stock to be sold \n
        :return: none
        """
        all_owned = self.portfolio["Ticker"].tolist()

        # Check if there is enough
        if all_owned.count(ticker) < quantity:
            print("Not enough stock owned")
            return False
        
        for id_num, row in self.portfolio.iterrows():
            if row["Ticker"] == ticker:
                current_price = row["Current Price"]

                self.update_balance(current_price)
                self.portfolio.drop(id_num, inplace=True)
        
        self.save()
        return self.portfolio
            
    
    def update_balance(self, amount):
        """
        Change balance

        :param amount: amount change
        :return: None
        """
        last_balance = float(self.balance)
        current_balance = last_balance + amount

        # Update the balanace sheet
        self.balance_sheet.close()
        self.balance_sheet = open(self.balance_sheet_name, "w+")
        self.balance_sheet.write(str(current_balance))

        # Update the local balance variable
        self.balance = current_balance

    def save(self):
        """
        Save portfolio

        :return: None
        """
        self.portfolio.to_csv(self.portfolio_name)
