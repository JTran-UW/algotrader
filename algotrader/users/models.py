from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from lib.YahooScraper import YahooScraper

y = YahooScraper()

# Create your models here.

class TradingManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not username:
            raise ValueError("Users must have a username")

        user = self.model(
            email=self.normalize_email(email),
            username=username
            )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username
            )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Trader(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    balance = models.FloatField(default=10000.0)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = TradingManager()

    def __str__(self):
        return self.username
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return True

    # My methods
    def buy(self, stock):
        """
        Purchase a share

        :param stock: stock to buy
        :param price_purchased: price of stock
        :return: Transaction object
        """
        # Create new transaction
        price_purchased = y.get_stock_price(stock)
        new_transaction = Transaction.objects.create(
            owner=self,
            stock=stock, 
            price_purchased=price_purchased
            )
        new_transaction.save()

        # Update balance
        self.balance -= price_purchased
        self.save()
        return new_transaction
    
    def sell(self, id):
        """
        """
        transaction = Transaction.objects.get(pk=id)
        price_sold = y.get_stock_price(transaction.stock)

        # Change transaction fields
        transaction.sold = True
        transaction.price_sold = price_sold
        transaction.date_sold = timezone.now()
        transaction.save()

        # Change balance
        self.balance += price_sold
        self.save()
        # TODO change values including date sold, price sold, balance
    
    def delete(self, id):
        """
        """
        transaction = Transaction.objects.get(pk=id)
        transaction.delete()

    def get_transactions(self, **kwargs):
        """
        Get all transactions

        :kwarg currently_owned: get only currently owned transactions (default: False)
        :return: QuerySet of filtered Transactions
        """
        currently_owned = kwargs.get("currently_owned", False)
        if currently_owned:
            filtered = Transaction.objects.filter(owner=self, sold=False)
        else:
            filtered = Transaction.objects.filter(owner=self)

        return filtered

class Transaction(models.Model):
    owner = models.ForeignKey("Trader", on_delete=models.CASCADE)
    stock = models.CharField(max_length=10)
    price_purchased = models.FloatField()
    date_purchased = models.DateTimeField(verbose_name="date purchased", auto_now_add=True)
    price_sold = models.FloatField(blank=True, null=True)
    date_sold = models.DateTimeField(blank=True, null=True)
    sold = models.BooleanField(default=False)
    