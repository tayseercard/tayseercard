from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from apps.vouchers.models import Voucher, VoucherScan
import json


def caissier_or_manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_admin() or request.user.is_manager() or request.user.is_caissier():
            return view_func(request, *args, **kwargs)
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')
    return wrapper


@login_required
@caissier_or_manager_required
def scan_page(request):
    """QR scanner page — uses html5-qrcode JS library."""
    return render(request, 'scanning/scan.html')


@login_required
@caissier_or_manager_required
def validate_voucher(request):
    """
    AJAX endpoint called after QR scan.
    Receives the voucher UUID and validates the voucher for activation or redemption.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée.'}, status=405)

    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Données invalides.'}, status=400)

    try:
        voucher = Voucher.objects.get(code=code)
    except Voucher.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'message': 'Voucher introuvable. QR code invalide.',
        })

    # Access control: caissier/manager can only scan their own store's vouchers
    user = request.user
    if not user.is_admin():
        user_store = user.get_store()
        if hasattr(user_store, 'filter'):  # ManyToMany
            user_store = user_store.first()
        if not user_store or user_store != voucher.store:
            return JsonResponse({
                'valid': False,
                'message': 'Ce voucher n\'appartient pas à votre magasin.',
            })

    # Check expiry
    if voucher.expires_at and voucher.expires_at < timezone.now():
        VoucherScan.objects.create(voucher=voucher, scanned_by=user, is_valid=False, notes='Expiré')
        return JsonResponse({
            'valid': False,
            'message': f'Voucher expiré le {voucher.expires_at.strftime("%d/%m/%Y")}.',
        })

    # Check status
    if voucher.status == Voucher.Status.USED:
        return JsonResponse({
            'valid': False,
            'message': 'Ce voucher a déjà été utilisé.',
        })

    if voucher.status == Voucher.Status.CANCELLED:
        return JsonResponse({
            'valid': False,
            'message': 'Ce voucher est annulé.',
        })

    if voucher.status == Voucher.Status.BLANK:
        # Blank vouchers are valid for activation by cashier/manager.
        VoucherScan.objects.create(voucher=voucher, scanned_by=user, is_valid=True, notes='Voucher vide détecté')
        return JsonResponse({
            'valid': True,
            'message': 'Ce voucher est vide. Vous pouvez l\'activer maintenant.',
            'fill_url': reverse('voucher_fill', args=[voucher.pk]),
            'voucher': {
                'title': voucher.title,
                'value': str(voucher.value),
                'store': voucher.store.name,
                'status': 'BLANK',
            }
        })

    if not voucher.is_active:
        return JsonResponse({
            'valid': False,
            'message': 'Ce voucher est inactif.',
        })

    # Active voucher is valid and can be consumed multiple times until remaining value reaches 0.
    VoucherScan.objects.create(voucher=voucher, scanned_by=user, is_valid=True)

    return JsonResponse({
        'valid': True,
        'message': f'✅ Voucher actif. Solde restant : {voucher.remaining_value} DZD.',
        'redeem_url': reverse('voucher_redeem', args=[voucher.pk]),
        'voucher': {
            'title': voucher.title,
            'value': str(voucher.value),
            'remaining_value': str(voucher.remaining_value),
            'store': voucher.store.name,
            'status': 'ACTIVE',
        }
    })


@login_required
@caissier_or_manager_required
def scan_history(request):
    """Show today's scans for this user."""
    today = timezone.now().date()
    user = request.user

    if user.is_admin():
        scans = VoucherScan.objects.all()
    elif user.is_manager():
        store = user.get_store()
        scans = VoucherScan.objects.filter(voucher__store=store)
    else:
        scans = VoucherScan.objects.filter(scanned_by=user)

    scans_today = scans.filter(scanned_at__date=today).select_related('voucher', 'scanned_by')
    return render(request, 'scanning/history.html', {
        'scans': scans_today,
        'today': today,
    })
