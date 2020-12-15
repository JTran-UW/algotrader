from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn import metrics

import pandas as pd
from TradingClient import TradingClient
from YahooScraper import YahooScraper

class TradingInterface():
    def __init__(self, watchlist_name, xpath_name, portfolio_name, predict_name, balance_sheet):
        """
        Interface for scraping data, making predictions, and trading

        :param watchlist_name: string of watchlist file name, for use by scraper
        :param xpath_name: string of xpath file name, for use by scraper
        :param portfolio_name: string of portfolio file name, for use by trader
        :param predict_name: string of prediction file name, for use by data model
        :param balance_sheet: string of balance sheet name, for use by trader
        """
        self.watchlist_name = watchlist_name
        self.predict_name = predict_name

        self.trading_client = TradingClient(portfolio_name, balance_sheet)
        self.yahoo_scraper = YahooScraper(watchlist_name, xpath_name)

    def get_watchlist_price(self):
        """
        Get and write prices for the entire watchlist

        :return: list containing all prices
        """
        watchlist = self.yahoo_scraper.get_watchlist()
        pricelist = list()
        
        for i, stock in enumerate(watchlist):
            price = self.yahoo_scraper.get_stock_price(stock)
            pricelist.append(price)
            print(f"Price for {stock} is {price}")

            progress = (i / len(watchlist)) * 100
            progress = round(progress, 2)
            print(f"{progress}% completed...")
            
        self.yahoo_scraper.create_columns(["Price"], values=pricelist)
        self.yahoo_scraper.save()
        return pricelist
    
    def today_change(self):
        """
        Add today's % change change to watchlist

        :return: list containing percent changes
        """
        watchlist = self.yahoo_scraper.get_watchlist()
        changelist = list()

        for stock in watchlist:
            tdy = self.yahoo_scraper.stocks.at[stock, "Price"]
            ytd = self.yahoo_scraper.stocks.at[stock, "Close Today - 1"]
            change = (tdy / ytd) * 100 - 100
            changelist.append(change)
        
        self.yahoo_scraper.clear_columns(["Price"])
        self.yahoo_scraper.create_columns(["Today % Change"], values=changelist)
        self.yahoo_scraper.save()
        return changelist

    def make_prediction(self, result_column):
        """
        Use Random Forest Regressor to predict stock movements

        :result_column: name of prediction output column
        :return: list of all % change predictions
        """
        watch = pd.read_csv(self.watchlist_name, index_col="Symbol")
        predict = pd.read_csv(self.predict_name, index_col="Symbol")

        # Separate watchlist and predictions
        X = watch.iloc[:, 0: -2].values # Train attributes
        y = watch.iloc[:, -1].values # Train targets
        X_test = predict.iloc[:, 0:-1].values # Predict attributes

        # Scale attributes
        sc = StandardScaler()
        X = sc.fit_transform(X)
        X_test = sc.transform(X_test)

        # Open Regressor and make predictions
        regressor = RandomForestRegressor(n_estimators=200, random_state=0)
        regressor.fit(X, y)
        y_pred = regressor.predict(X_test)

        # Output predictions to the predict file
        predict[result_column] = y_pred
        predict.to_csv(self.predict_name)
        return y_pred
    
    def get_top_predictions(self, result_name, n):
        """
        Get top n predictions from prediction file

        :param result_name: name of prediction column
        :param n: int number of results to show
        :return: list of stock tickers
        """
        predict = pd.read_csv(self.predict_name, index_col="Symbol")
        predict = predict.sort_values(by=[result_name], ascending=False)
        predict = predict.index[:n]
        return predict
    
    def purchase_portfolio(self, stocks, **kwargs):
        """
        Purchase a number of stocks in client

        :param stocks: list of stocks to purchase
        :return: summary of stocks purchased
        """
        summary = []
        quantity = kwargs.get("quantity", [1] * len(stocks))

        for i, stock in enumerate(stocks):
            price = self.yahoo_scraper.get_stock_price(stock)
            self.trading_client.buy(stock, price, quantity[i])
            summary.append(self.trading_client.stock_summary(stock))
        
        return summary
    
    def summary(self):
        """
        Refresh portfolio and get summary

        :return: dictionary of leading summary indicators
        """
        price_db = {}
        portfolio = self.trading_client.portfolio

        for id_num, row in portfolio.iterrows():
            ticker = row["Ticker"]
            price = self.yahoo_scraper.get_stock_price(ticker)
            price_db[ticker] = price
        
        self.trading_client.refresh(price_db)
        return self.trading_client.portfolio_summary()

t = TradingInterface("data/watch.csv", "data/xpath.json", "data/model.csv", "data/predict.csv", "data/balance_sheet.txt")

print("Creating predictions...")
t.make_prediction("Today % Change")
predictions = t.get_top_predictions("Today % Change", 25)

print("Purchasing predictions")
print(t.purchase_portfolio(predictions))
