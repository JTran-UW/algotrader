from django.shortcuts import render, redirect
from lib.YahooScraper import YahooScraper
from math import floor

y = YahooScraper()

# Create your views here.

def stock_view(request):
    if request.method == "POST":
        stock = request.POST["stock"]
        return redirect(f"/stock/{stock}")
    else:
        return render(request, "trades/stock.html")

def stock_search_view(request, **kwargs):
    ticker = kwargs.get("ticker")

    if request.method == "POST":
        if request.user.is_authenticated:
            stock = request.POST["stock"]
            quantity = request.POST["quantity"]

            price = y.get_stock_price(stock)
            for i in range(int(quantity)):
                request.user.buy(stock, price)

            return redirect("profile")
        else:
            return redirect("login")
    else:
        price = y.get_stock_price(ticker)
        historical = y.get_historical([ticker])
        daterange = list(historical.index)
        close = [float(n) for n in list(historical["Close"])]

        if (request.user.is_authenticated):
            max_quant = floor(request.user.balance/price)
        else:
            max_quant = 1
        
        data = {
            "ticker": ticker,
            "price": price,
            "daterange": daterange,
            "close": close,

            "max_quant": max_quant
        }

    return render(request, "trades/search.html", {"data": data})
