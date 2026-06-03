from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Voucher, VoucherRequest
from .forms import VoucherRequestForm, VoucherFillForm, VoucherPriceForm
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField
from apps.stores.models import Store


def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_manager():
            messages.error(request, "Accès réservé aux managers.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_or_caissier_required(view_func):
    """Allow access to managers or caissiers (store employees)."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_manager() or request.user.is_caissier()):
            messages.error(request, "Accès réservé aux managers et caissiers.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_user_store(user):
    """Return the store owned or assigned to this user."""
    if user.is_admin():
        return None
    if user.is_manager():
        store = getattr(user, 'managed_store', None)
        if store:
            return store
        return Store.objects.filter(manager=user).first()
    if user.is_caissier():
        caissier_store = getattr(user, 'caissier_store', None)
        if hasattr(caissier_store, 'first'):
            return caissier_store.first()
        return caissier_store
    return None


# ─── MANAGER VIEWS ────────────────────────────────────────────────

@login_required
@manager_required
def voucher_request_create(request):
    """Manager submits a voucher request for admin approval."""
    store = request.user.get_store()
    if not store:
        messages.error(request, "Aucun magasin associé.")
        return redirect('manager_dashboard')

    form = VoucherRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        vr = form.save(commit=False)
        vr.store = store
        vr.requested_by = request.user
        vr.status = VoucherRequest.Status.PENDING
        vr.save()
        messages.success(request, "Demande envoyée. En attente d'approbation.")
        return redirect('voucher_request_list')

    return render(request, 'vouchers/request_create.html', {'form': form, 'store': store})


@login_required
@manager_required
def voucher_request_list(request):
    """Manager sees his own requests and their status."""
    store = request.user.get_store()
    requests_qs = VoucherRequest.objects.filter(store=store).order_by('-created_at')
    return render(request, 'vouchers/request_list.html', {
        'requests': requests_qs,
        'store': store,
    })


@login_required
def voucher_list(request):
    """List approved/active vouchers."""
    user = request.user
    status_filter = request.GET.get('status', '')
    buyer_filter = request.GET.get('buyer', '')
    beneficiary_filter = request.GET.get('beneficiary', '')

    if user.is_admin():
        qs = Voucher.objects.select_related('store')
    else:
        store = get_user_store(user)
        qs = Voucher.objects.filter(store=store) if store else Voucher.objects.none()
        if user.is_caissier():
            qs = qs.exclude(status=Voucher.Status.BLANK)
        else:
            # For store managers: hide BLANK vouchers whose access period has expired
            # (ACTIVE vouchers are never hidden — the client has already been served)
            qs = qs.exclude(
                status=Voucher.Status.BLANK,
                expires_at__lt=timezone.now()
            )

    if status_filter:
        qs = qs.filter(status=status_filter)
    if buyer_filter:
        qs = qs.filter(customer_name__icontains=buyer_filter)
    if beneficiary_filter:
        qs = qs.filter(beneficiary_name__icontains=beneficiary_filter)

    vouchers = qs.annotate(
        status_priority=Case(
            When(status='ACTIVE', then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by('-updated_at')

    paginator = Paginator(vouchers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vouchers/list.html', {
        'vouchers': page_obj,
        'status_filter': status_filter,
        'buyer_filter': buyer_filter,
        'beneficiary_filter': beneficiary_filter,
    })


@login_required
def voucher_detail(request, pk):
    voucher = get_object_or_404(Voucher, pk=pk)
    user = request.user
    if not user.is_admin():
        user_store = get_user_store(user)
        if not user_store or user_store != voucher.store:
            messages.error(request, "Accès refusé.")
            return redirect('dashboard')
    return render(request, 'vouchers/detail.html', {'voucher': voucher})


@login_required
@manager_required
def voucher_print(request, pk):
    store = request.user.get_store()
    voucher = get_object_or_404(Voucher, pk=pk, store=store)
    return render(request, 'vouchers/print.html', {'voucher': voucher})


@login_required
@manager_or_caissier_required
def voucher_fill(request, pk):
    """Manager activates a BLANK voucher by filling client/value details."""
    store = get_user_store(request.user)
    voucher = get_object_or_404(Voucher, pk=pk, store=store, status=Voucher.Status.BLANK)

    form = VoucherFillForm(request.POST or None, instance=voucher)
    # Block if expired
    if voucher.expires_at and timezone.now() > voucher.expires_at:
        messages.error(request, "Ce voucher a expiré. Il ne peut plus être activé.")
        return redirect('voucher_detail', pk=voucher.pk)
    if request.method == 'POST' and form.is_valid():
        v = form.save(commit=False)
        v.status = Voucher.Status.ACTIVE
        v.is_active = True
        v.remaining_value = v.value  # Initialize remaining balance = full value
        v.updated_by = request.user
        v.save()
        messages.success(request, "Voucher rempli et activé avec succès.")
        return redirect('voucher_detail', pk=voucher.pk)

    return render(request, 'vouchers/fill.html', {'form': form, 'voucher': voucher})


@login_required
@manager_or_caissier_required
def voucher_redeem(request, pk):
    """Manager redeems (partially or fully) an ACTIVE voucher for beneficiary."""
    store = get_user_store(request.user)
    voucher = get_object_or_404(Voucher, pk=pk, store=store, status=Voucher.Status.ACTIVE)

    error = None
    # ACTIVE vouchers are NEVER blocked by expiry — client has already paid
    if request.method == 'POST':
        entered_pin = request.POST.get('pin_code', '').strip()
        amount_str = request.POST.get('amount', '').strip()

        # PIN check (only if a PIN was set)
        if voucher.pin_code and entered_pin != voucher.pin_code:
            error = "Code PIN incorrect."
        else:
            try:
                from decimal import Decimal, InvalidOperation
                amount = Decimal(amount_str)
                if amount <= 0:
                    error = "Le montant doit être supérieur à 0."
                elif amount > voucher.remaining_value:
                    error = f"Montant insuffisant. Solde restant : {voucher.remaining_value} DA"
                else:
                    voucher.remaining_value -= amount
                    if voucher.remaining_value <= 0:
                        voucher.remaining_value = 0
                        voucher.status = Voucher.Status.USED
                        voucher.is_active = False
                    voucher.updated_by = request.user
                    voucher.save()
                    messages.success(request, f"{amount} DA consommés. Solde restant : {voucher.remaining_value} DA.")
                    return redirect('voucher_detail', pk=voucher.pk)
            except (ValueError, InvalidOperation):
                error = "Montant invalide."

    return render(request, 'vouchers/redeem.html', {
        'voucher': voucher,
        'error': error,
        'has_pin': bool(voucher.pin_code),
    })


@login_required
@admin_required
def pack_list(request):
    """Admin manages VoucherPrice packs."""
    from .models import VoucherPrice
    packs = VoucherPrice.objects.order_by('price')
    return render(request, 'vouchers/pack_list.html', {'packs': packs})


@login_required
@admin_required
def pack_create(request):
    """Admin creates a new voucher pack."""
    form = VoucherPriceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Pack créé avec succès.")
        return redirect('pack_list')
    return render(request, 'vouchers/pack_form.html', {'form': form, 'title': 'Nouveau pack'})


@login_required
@admin_required
def pack_edit(request, pk):
    """Admin edits an existing voucher pack."""
    from .models import VoucherPrice
    pack = get_object_or_404(VoucherPrice, pk=pk)
    form = VoucherPriceForm(request.POST or None, instance=pack)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Pack mis à jour.")
        return redirect('pack_list')
    return render(request, 'vouchers/pack_form.html', {'form': form, 'title': 'Modifier le pack', 'pack': pack})


# ─── ADMIN VIEWS ──────────────────────────────────────────────────

@login_required
@admin_required
def admin_request_list(request):
    """Admin sees all pending voucher requests."""
    status_filter = request.GET.get('status', 'PENDING')
    requests_qs = VoucherRequest.objects.select_related(
        'store', 'requested_by'
    ).filter(status=status_filter).order_by('-created_at')

    return render(request, 'vouchers/admin_request_list.html', {
        'requests': requests_qs,
        'status_filter': status_filter,
    })


@login_required
@admin_required
def admin_request_detail(request, pk):
    """Admin reviews a voucher request — approve or reject."""
    vr = get_object_or_404(VoucherRequest, pk=pk)
    today = timezone.now().date().isoformat()
    return render(request, 'vouchers/admin_request_detail.html', {'vr': vr, 'today': today})


@login_required
@admin_required
def admin_request_approve(request, pk):
    """Approve request → generate vouchers with QR codes (6-month expiry)."""
    vr = get_object_or_404(VoucherRequest, pk=pk, status=VoucherRequest.Status.PENDING)

    if request.method == 'POST':
        from datetime import timedelta

        # Auto-set expiration to 6 months (~183 days) from now
        expires_at = timezone.now() + timedelta(days=183)

        vr.status = VoucherRequest.Status.APPROVED
        vr.reviewed_by = request.user
        vr.reviewed_at = timezone.now()
        vr.expires_at = expires_at
        vr.save()

        # Generate vouchers with 6-month expiry
        total_vouchers = vr.quantity * vr.price_template.pack_quantity
        for _ in range(total_vouchers):
            Voucher.objects.create(
                request=vr,
                store=vr.store,
                title="",
                description=vr.price_template.description,
                value=0,
                price=vr.price_template.price,
                status=Voucher.Status.BLANK,
                is_active=False,
                expires_at=expires_at,
                created_by=request.user,
            )

        expires_str = expires_at.strftime('%d/%m/%Y')
        messages.success(request, f"{total_vouchers} voucher(s) créés pour {vr.store.name}. Valables jusqu'au {expires_str}.")

        # Renewal: restore access to previously expired BLANK vouchers of this store
        restored = Voucher.objects.filter(
            store=vr.store,
            status=Voucher.Status.BLANK,
            expires_at__lt=timezone.now()
        ).update(expires_at=expires_at)
        if restored:
            messages.info(request, f"{restored} bon(s) vide(s) dont la période avait expiré ont été restaurés avec la nouvelle date.")

        return redirect('admin_request_list')

    return redirect('admin_request_detail', pk=pk)


@login_required
@admin_required
def admin_request_reject(request, pk):
    """Reject a voucher request with a reason."""
    vr = get_object_or_404(VoucherRequest, pk=pk, status=VoucherRequest.Status.PENDING)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        vr.status = VoucherRequest.Status.REJECTED
        vr.rejection_reason = reason
        vr.reviewed_by = request.user
        vr.reviewed_at = timezone.now()
        vr.save()
        messages.success(request, "Demande rejetée.")
        return redirect('admin_request_list')

    return redirect('admin_request_detail', pk=pk)