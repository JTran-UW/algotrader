import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

class YahooScraper:
    def __init__(self):
        """
        A web scraping tool to gather essential stock information from Yahoo Finance
        """
        self.headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36"
        }

    def get_tables(self, link):
        """
        Get all tables in Yahoo Finance page\n
        
        :param link: str link to page\n
        :return: list of dataframes containing scraped info
        """
        html = requests.get(link, headers=self.headers)
        print(html.status_code)
        soup = BeautifulSoup(html.content, "html.parser")
        tables = soup.find_all("table")
        dfs = []

        for table in tables:
            df = pd.read_html(str(table), index_col=0)[0]
            dfs.append(df)
        
        return dfs

    def get_summary(self, stocks):
        """
        Scrape Yahoo Finance for summary data\n
        
        :param stocks: list of stock tickers\n
        :return: dataframe of resulting data
        """
        summary = []
        for stock in stocks:
            link = f"https://finance.yahoo.com/quote/{stock}?p={stock}"
            tables = self.get_tables(link)

            table = pd.concat(tables).T
            table.index = [stock]
            summary.append(table)
        
        return pd.concat(summary)

    def get_statistics(self, stocks):
        """
        Scrape Yahoo Finance for stock statistics\n
        
        :param stocks: list of stock tickers\n
        :return: dataframe of resulting data
        """
        statistics = []
        for stock in stocks:
            link = f"https://finance.yahoo.com/quote/{stock}/key-statistics?p={stock}"
            dfs = self.get_tables(link)[1:]

            values = pd.concat(dfs).T
            values.rename(index={1: stock}, inplace=True)
            statistics.append(values)
        
        return pd.concat(statistics)

    def get_historical(self, stocks, **kwargs):
        """
        Scrape Yahoo Finance for historical data\n
        
        :param stocks: list of stock tickers\n
        :kwarg period1: minimum range of data (datetime object)\n
        :kwarg period2: maximum range of data (datetime object)\n
        :kwarg interval: interval of data (d: daily, wk: weekly, mo: monthly)\n
        :kwarg oneline: return dataframe as 1 row per stock\n
        :return: dataframe of resulting data
        """
        # Handle kwargs
        today = datetime.today() - datetime(1970, 1, 1)
        today = round(today.total_seconds())
        period1 = kwargs.get("period1", today - 31536000) # Today - 1 year
        period2 = kwargs.get("period2", period1 + 31536000) # Min bound + 1 year
        interval = kwargs.get("interval", "d")
        oneline = kwargs.get("oneline", False)

        if not oneline and len(stocks) > 1:
            raise Exception("Multi-line output only available for one stock at a time")

        historical = []
        for stock in stocks:
            link = f"https://query1.finance.yahoo.com/v7/finance/download/{stock}?period1={period1}&period2={period2}&interval=1{interval}"
            data = requests.get(link, stream=True, headers=self.headers).text
            data = data.split("\n")
            data = [row.split(",") for row in data]

            df = pd.DataFrame(data[1:], columns=data[0])
            df = df.set_index("Date")
            
            if oneline:
                indices = []
                for index, row in df.iterrows():
                    for col in df.columns:
                        indices.append(f"{col} - {row.name}")
                df = df.values.flatten()
                historical.append(pd.DataFrame([df], index=[stock], columns=indices))
            else:
                return df
        
        return pd.concat(historical)
                

    def get_financials(self, stocks):
        pass

    def get_analysis(self, stocks, **kwargs):
        """
        Scrape Yahoo Finance for analyist data\n
        
        :param stocks: list of stock tickers\n
        :kwarg timeframe: column to scrape ('cq': current quarter, 'nq': next quarter, 'cy': current year, 'ny': next year)\n
        :return: dataframe of resulting data
        """
        # Handle timeframe keyword arguments
        timeframe = kwargs.get("timeframe", "cq")
        if timeframe =="nq":
            col = 1
        elif timeframe == "cy":
            col = 2
        elif timeframe == "ny":
            col = 3
        else:
            col = 0

        analysis = []
        for stock in stocks:
            dfs = []
            link = f"https://finance.yahoo.com/quote/{stock}/analysis?p={stock}"
            for table in self.get_tables(link):
                # Get new index names (to differentiate)
                title = table.index.name
                indices = [f"{row} - {title}" for row in table.index]
                
                # Rename indices and columns
                table = table.iloc[:, [col]]
                table.index = indices
                table.columns = [stock]
                dfs.append(table)
            
            analysis.append(pd.concat(dfs).T)
            
        return pd.concat(analysis)
    
    def get_stock_price(self, ticker):
        """
        Scrapes Yahoo Finance for the price of some stock\n
        
        :param ticker: symbol of stock\n
        :return: float price of stock
        """
        link = f"https://finance.yahoo.com/quote/{ticker}?p={ticker}"
        overview = requests.get(link)
        soup = BeautifulSoup(overview.content, "html.parser")

        css_selector = "#quote-header-info > div.My\(6px\).Pos\(r\).smartphone_Mt\(6px\) > div.D\(ib\).Va\(m\).Maw\(65\%\).Ov\(h\) > div > span.Trsdu\(0\.3s\).Fw\(b\).Fz\(36px\).Mb\(-4px\).D\(ib\)"
        price = soup.select(css_selector)[0]
        price = price.getText().replace(",", "")
        return float(price)
    
    def save(self, stocks, filename):
        """
        Write stocks to filename as a csv file\n

        :param stocks: list of stock tickers\n
        :param filename: name of file\n
        """
        stocks.to_csv(filename)

y = YahooScraper()
print(y.get_historical(["AAPL"]))
