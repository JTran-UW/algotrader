from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Trader, Transaction

# Register your models here.

class TradingAdmin(UserAdmin):
    list_display = ("email", "username", "date_joined", "last_login", "is_admin", "is_staff")
    search_fields = ("email", "username")
    readonly_fields = ("date_joined", "last_login")

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

class TransactionAdmin(admin.ModelAdmin):
    readonly_fields = ("owner", "stock", "price_purchased", "date_purchased", "sold")

admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Trader, TradingAdmin)
