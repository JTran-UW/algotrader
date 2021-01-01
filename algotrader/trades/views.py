from django.shortcuts import render, redirect

# Create your views here.

def stock_view(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            stock = request.POST["stock"]
            request.user.buy(stock)

            return redirect("profile")
        else:
            return redirect("login")
    else:
        return render(request, "trades/stock.html")
