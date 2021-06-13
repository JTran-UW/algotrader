from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, TraderAuthenticationForm

# Create your views here.
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})

def login_view(request):
    user = request.user
    if user.is_authenticated:
        return redirect("profile")
    
    if request.POST:
        form = TraderAuthenticationForm(request.POST)
        if form.is_valid():
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(username=username, password=password)

            if user:
                login(request, user)
                return redirect("profile")
    else:
        form = TraderAuthenticationForm()
    return render(request, "users/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def profile_view(request):
    if request.method == "POST":
        submit = request.POST["submit"]
        id = request.POST["id"]
        if submit == "Delete":
            request.user.delete(id)
        else:
            request.user.sell(id)

    transactions = request.user.get_transactions()
    transactions = list(reversed(transactions))

    owned_ts = [t for t in transactions if not t.sold]
    sold_ts = [t for t in transactions if t.sold]
    balance = "{:.2f}".format(request.user.balance)

    return render(request, "users/profile.html", {"owned_ts": owned_ts,
                                                  "sold_ts": sold_ts, 
                                                  "balance": balance})
