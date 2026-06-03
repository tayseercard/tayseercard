from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.models import User
from apps.stores.models import Store, StorePartnerRequest
from apps.vouchers.models import Voucher, VoucherScan, VoucherRequest, VoucherPrice


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


@admin.register(VoucherPrice)
class VoucherPriceAdmin(admin.ModelAdmin):
    list_display = ['title', 'value', 'price', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'description', 'is_active')
        }),
        ('Tarification', {
            'fields': ('value', 'price')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


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


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['title', 'store', 'value', 'price', 'status', 'is_active', 'created_at']
    list_filter = ['status', 'is_active', 'store']
    search_fields = ['title', 'store__name', 'code']
    readonly_fields = ['code', 'qr_image', 'created_at']

    def has_add_permission(self, request):
        # Vouchers should be created through the app, not admin
        return request.user.is_superuser


@admin.register(VoucherScan)
class VoucherScanAdmin(admin.ModelAdmin):
    list_display = ['voucher', 'scanned_by', 'scanned_at', 'is_valid']
    list_filter = ['is_valid', 'scanned_at']
    readonly_fields = ['voucher', 'scanned_by', 'scanned_at']
