from apps.vouchers.models import VoucherRequest


def admin_notifications(request):
    pending_requests = 0
    if request.user.is_authenticated:
        is_admin = getattr(request.user, 'is_admin', False)
        if callable(is_admin):
            is_admin = is_admin()
        if is_admin:
            pending_requests = VoucherRequest.objects.filter(status=VoucherRequest.Status.PENDING).count()
    return {
        'pending_requests': pending_requests,
    }
