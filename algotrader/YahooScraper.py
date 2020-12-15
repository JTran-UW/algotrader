import pandas as pd
import requests
from lxml import html
import json

class YahooScraper:
    def __init__(self, output, xpath):
        """
        YahooScraper is a web scraping tool that gets stock data from Yahoo Finance.

        :param output: Name of output file
        """
        self.out_file = output
        self.path_file = xpath

        try:
            self.stocks = pd.read_csv(self.out_file, index_col="Symbol")
        except FileNotFoundError:
            print(f"No watchlist file with name '{output}' was found, exiting...")
            return None

        # Create columns
        fund_labels = self.load_paths("Fundamentals").keys()
        week_labels = self.load_paths("Week Info").keys()
        labels = list(fund_labels) + list(week_labels)
        self.stocks = self.create_columns(labels)

    def create_columns(self, columns, **kwargs):
        """
        Adds missing columns to self.stocks

        :param columns: list of column names
        :kwarg values: list of column values (default: all zeroes)
        :return: resultant DataFrame
        """
        col_names = columns
        default_values = [0.0] * self.stocks.shape[0]
        values = kwargs.get("values", default_values)

        for elem in col_names:
            if elem not in self.stocks.columns:
                self.stocks[elem] = pd.Series(values, index=self.stocks.index)
                print(f"{elem} not found, creating...")
        
        return self.stocks

    def create_rows(self, rows):
        """
        Adds missing rows to self.stocks

        :param rows: list of row names
        :return: resultant DataFrame
        """
        row_names = rows
        size = self.stocks.shape[1]
        
        for elem in row_names:
            if elem not in self.stocks.rows:
                self.stocks.loc[elem] = pd.Series([None] * size, index=self.stocks.index)
                print(f"{elem} not found, creating...")
        
        return self.stocks
    
    def clear_columns(self, columns):
        """
        Clear a number of columns

        :param columns: list of column names
        :return: resultant DataFrame
        """
        col_names = columns
        size = self.stocks.shape[0]

        for elem in col_names:
            if elem in self.stocks.columns:
                del self.stocks[elem]
                print(f"Deleting {elem}...")
        
        return self.stocks

    def load_paths(self, section):
        """
        Load xpath json file

        :param section: name of section to access
        :return: dictionary of attributes and xpaths
        """
        try:
            with open(self.path_file, "r") as paths:
                xpath = json.load(paths)
                xpath = dict(xpath[section])
        except FileNotFoundError:
            print(f"No such file {self.path_file} found, exiting...")
            return None

        return xpath
    
    def to_float(self, string):
        """
        Convert string to float

        :param string: string to convert
        :return float: return float of string, or -1 if NoneType
        """
        n = string

        # Check if NoneType
        if n is None:
            print("!!! No such entry exists")
            n = -1
            return n

        # Remove all commas
        if len(n.split(",")) > 1:
            n = "".join(n.split(","))

        try:
            # Make result a float
            if n[-1] == "T":
                n = float(n[:-1]) * 1000000000000
            elif n[-1] == "B":
                n = float(n[:-1]) * 1000000000
            elif n[-1] == "M":
                n = float(n[:-1]) * 1000000
            elif n[-1] == "k":
                n = float(n[:-1]) * 1000
            elif n[-1] == "%":
                n = float(n[:-1])
            else:
                n = float(n)
        except ValueError:
            print(f"!!! Unknown input {n}")
            n = -1
        
        return n

    def five_day_change(self):
        """
        Update five day % change

        :return: stock watchlist
        """
        self.stocks = self.create_columns(["5 Day % Change"])

        for ticker, row in self.stocks.iterrows():
            ytday = row["Close Today - 1"]
            start = row["Open Today - 5"]

            if ytday == -1 or start == -1:
                print(f"Droppping {ticker}")
                self.stocks.drop([ticker])
            else:
                change = (ytday / start) * 100 - 100
                self.stocks.at[ticker, "5 Day % Change"] = change
        
        self.save()
        return self.stocks

    def scrape_fundamentals(self, ticker):
        """
        Scrape Yahoo Finance for stock fundamentals

        :param ticker: stock ticker
        :return: dictionary of results
        """
        paths = self.load_paths("Fundamentals")
        results = {}

        response = requests.get(f"https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}").content
        fundamentals = html.fromstring(response)

        for key in paths:
            try:
                path = paths[key]
                value = fundamentals.xpath(path)[0].text
                value = self.to_float(value)
                results[key] = value
            except IndexError:
                print("!!! Yahoo Finance has no information here")
                results[key] = -1
        
        return results

    def scrape_week_info(self, ticker):
        """
        Scrape Yahoo Finance for historical stock info

        :param ticker: stock ticker
        :return: dictionary of results
        """
        paths = self.load_paths("Week Info")
        results = {}

        response = requests.get(f"https://finance.yahoo.com/quote/{ticker}/history?p={ticker}").content
        history = html.fromstring(response)

        for key in paths:
            try:
                path = paths[key]
                value = history.xpath(path)[0].text
                value = self.to_float(value)
                results[key] = value
            except IndexError:
                print("!!! Yahoo Finance has no information here")
                results[key] = -1
        
        return results

    def get_stock_price(self, ticker):
        """
        Scrape Yahoo Finance for stock price
        
        :param ticker: stock ticker
        :return: price of stock
        """
        path = self.load_paths("Overview")["Price"]

        response = requests.get(f"https://finance.yahoo.com/quote/{ticker}/")
        html_res = html.fromstring(response.content)

        price = html_res.xpath(path)[0]
        price = float(price.text)
        return price
    
    def get_watchlist(self):
        """
        Get all stocks on watchlist

        :return: list of symbols
        """
        symbols = self.stocks.index
        return symbols

    def run(self, **kwargs):
        """
        Scrape Yahoo Finance for stock data

        :kwarg run_fundamentals: if false, will skip scraping fundamentals (default: true)
        :kwarg run_week: if false, will scape scraping week info (default: true)
        :kwarg columns: list of column names to append to dataframe (default: none)
        :return: None
        """
        i = 0
        size = self.stocks.shape[0]
        run_fund = kwargs.get("run_fundamentals", True)
        run_week = kwargs.get("run_week", True)

        for ticker, row in self.stocks.iterrows():
            if row.isnull().values.any():
                if run_fund:
                    fundamentals = self.scrape_fundamentals(ticker)
                else:
                    fundamentals = {}

                if run_week:
                    week_info = self.scrape_week_info(ticker)
                else: 
                    week_info = {}

                info = {**fundamentals, **week_info}
                columns = kwargs.get("columns", info)
                for key in columns:
                    self.stocks.at[ticker, key] = info[key]
                    print(f"Data entry at {key} for {ticker}: {info[key]}")
            else:
                print(f"!!! Values filled.  Passing {ticker}...")
            
            i += 1
            progress = round((i / size) * 100, 2)
            if progress % 10 == 0:
                print(f"{progress}% completed, saving...")
                self.save()
            else:
                print(f"{progress}% completed...")
        
        return self.stocks
    
    def save(self):
        """
        Save self.stocks to CSV file

        :return: None
        """
        self.stocks.to_csv(self.out_file)
