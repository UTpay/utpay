from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import *

UserAdmin.list_display = ('username', 'email', 'last_login', 'date_joined', 'is_active', 'is_staff')
UserAdmin.ordering = ('id',)

class EthAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'address', 'password', 'created_at', 'modified_at')
    list_filter = ('user', 'created_at', 'modified_at')
    ordering = ('id',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'eth_account', 'tx_hash', 'from_address', 'to_address', 'amount', 'gas', 'gas_price', 'value', 'network_id', 'is_active', 'created_at')
    list_filter = ('user', 'eth_account', 'from_address', 'to_address', 'amount', 'gas', 'gas_price', 'value', 'network_id', 'is_active', 'created_at')
    ordering = ('id',)

class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'address', 'password', 'name', 'is_active', 'is_verified', 'is_banned', 'verified_at', 'created_at', 'modified_at')
    list_filter = ('user', 'is_active', 'is_verified', 'is_banned', 'verified_at', 'created_at', 'modified_at')
    ordering = ('id',)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(EthAccount, EthAccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Contract, ContractAdmin)
