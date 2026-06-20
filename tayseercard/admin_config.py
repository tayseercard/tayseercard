
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.models import User
from apps.stores.models import Store, StorePartnerRequest
from apps.vouchers.models import Voucher, VoucherScan, VoucherRequest, VoucherPrice


# Register custom User admin only once
if not admin.site.is_registered(User):
    @admin.register(User)
    class UserAdmin(BaseUserAdmin):
        list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
        list_filter = ['role', 'is_active']
        fieldsets = BaseUserAdmin.fieldsets + (
            ('Rôle', {'fields': ('role',)}),
        )
        add_fieldsets = BaseUserAdmin.add_fieldsets + (
            ('Rôle', {'fields': ('role',)}),
        )


# Store admin registration moved to stores app (handled in apps/stores/admin.py)

# StorePartnerRequest admin is registered in apps/stores/admin.py


# VoucherPrice admin is registered in apps/vouchers/admin.py


@admin.register(VoucherRequest)
class VoucherRequestAdmin(admin.ModelAdmin):
    list_display = ['get_title', 'store', 'quantity', 'get_total', 'status', 'requested_by', 'created_at']
    list_filter = ['status', 'created_at', 'store']
    search_fields = ['price_template__title', 'store__name', 'requested_by__username']
    readonly_fields = ['requested_by', 'reviewed_by', 'created_at', 'reviewed_at', 'get_total']

    fieldsets = (
        ('Demande', {
            'fields': ('price_template', 'quantity', 'expires_at', 'get_total')
        }),
        ('Magasin & Demandeur', {
            'fields': ('store', 'requested_by')
        }),
        ('Approbation', {
            'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_title(self, obj):
        return obj.title
    get_title.short_description = 'Titre'

    def get_total(self, obj):
        return f"{obj.total_amount:.2f} DZD"
    get_total.short_description = 'Montant total'


# Voucher admin registration moved to apps/vouchers/admin.py (handled there)


@admin.register(VoucherScan)
class VoucherScanAdmin(admin.ModelAdmin):
    list_display = ['voucher', 'scanned_by', 'scanned_at', 'is_valid']
    list_filter = ['is_valid', 'scanned_at']
    readonly_fields = ['voucher', 'scanned_by', 'scanned_at']
