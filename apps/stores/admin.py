# d:/tayseercard/apps/stores/admin.py
from django.contrib import admin
from .models import Store, StorePartnerRequest

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'is_active', 'created_at', 'total_vouchers']
    list_filter = ['is_active']
    search_fields = ['name', 'manager__username']
    filter_horizontal = ['caissiers']

@admin.register(StorePartnerRequest)
class StorePartnerRequestAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'full_name', 'email', 'phone', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['store_name', 'email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'reviewed_at', 'reviewed_by']
