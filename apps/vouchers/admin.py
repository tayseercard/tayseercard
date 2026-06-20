from django.contrib import admin
from .models import VoucherPrice, Voucher

class AdminOnlyModelAdmin(admin.ModelAdmin):
    """Restrict admin access to users with role ADMIN or is_superuser."""
    def has_module_permission(self, request):
        return request.user.is_active and (request.user.is_superuser or request.user.is_admin())
    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)
    def has_add_permission(self, request):
        return self.has_module_permission(request)
    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)
    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

@admin.register(VoucherPrice)
class VoucherPriceAdmin(AdminOnlyModelAdmin):
    list_display = ("title", "value", "price", "pack_quantity", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description")
    ordering = ("price",)

@admin.register(Voucher)
class VoucherAdmin(AdminOnlyModelAdmin):
    list_display = ("title", "store", "price", "status", "created_at")
    list_filter = ("status", "store", "created_at")
    search_fields = ("title", "code")
    ordering = ("-created_at",)
