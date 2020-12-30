from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .lib.YahooScraper import YahooScraper

# Create your views here.

y = YahooScraper()

@login_required
def stock_view(request):
    if request.method == "POST":
        stock = request.POST["stock"]
        price_purchased = y.get_stock_price(stock)
        request.user.buy(stock, price_purchased)

        return redirect("home")
    else:
        return render(request, "trades/stock.html")
