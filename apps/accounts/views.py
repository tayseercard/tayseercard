from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.utils import timezone
from .models import User, SitePolicy
from .forms import LoginForm, CaissierCreateForm, CaissierEditForm, AccountSettingsForm, TermsForm

def render_account_access_error(request, title, message):
    return render(request, 'accounts/access_error.html', {
        'title': title,
        'message': message,
    })


def home(request):
    """Landing page with info and prices."""
    from apps.vouchers.models import VoucherPrice
    packs = VoucherPrice.objects.filter(is_active=True).order_by('price')
    return render(request, 'home.html', {
        'packs': packs,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user_obj = User.objects.filter(email__iexact=email).first()
        username = user_obj.username if user_obj else email

        user = authenticate(
            request,
            username=username,
            password=password,
        )
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            if user_obj and not user_obj.is_active:
                if user_obj.check_password(password):
                    messages.error(request, "Votre compte est en cours d'examen. Il doit être approuvé par un administrateur.")
                else:
                    messages.error(request, "Identifiants incorrects.")
            else:
                messages.error(request, 'Identifiants incorrects.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """Redirect each role to their own dashboard."""
    user = request.user
    if user.is_admin():
        return redirect('admin_dashboard')
    elif user.is_manager():
        return redirect('manager_dashboard')
    elif user.is_caissier():
        return redirect('caissier_dashboard')
    return redirect('login')


@login_required
def admin_dashboard(request):
    if not request.user.is_admin():
        return redirect('dashboard')

    from apps.stores.models import Store, StorePartnerRequest
    from apps.vouchers.models import Voucher, VoucherScan, VoucherRequest
    from django.db.models import Count, Sum
    from django.db.models.functions import TruncDay
    from datetime import timedelta

    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)

    # Basic stats
    total_stores = Store.objects.count()
    total_vouchers = Voucher.objects.count()
    used_vouchers = Voucher.objects.filter(status='USED').count()
    scans_today = VoucherScan.objects.filter(scanned_at__date=today).count()

    # Revenue Calculation
    total_rev = 0
    approved_reqs = VoucherRequest.objects.filter(status='APPROVED').select_related('price_template')
    for req in approved_reqs:
        if req.price_template:
            total_rev += (req.price_template.price * req.quantity)

    # Pending requests count
    pending_requests = VoucherRequest.objects.filter(status='PENDING').count()
    pending_store_requests = StorePartnerRequest.objects.filter(status='PENDING').count()

    # Chart 1: Evolution of scans (last 7 days)
    scans_evolution = VoucherScan.objects.filter(
        scanned_at__date__gte=seven_days_ago
    ).annotate(day=TruncDay('scanned_at')).values('day').annotate(count=Count('id')).order_by('day')
    
    scan_labels = []
    scan_counts = []
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        scan_labels.append(day.strftime('%d %b'))
        count = next((item['count'] for item in scans_evolution if item['day'].date() == day), 0)
        scan_counts.append(count)

    # Chart 2: Status distribution
    status_counts = Voucher.objects.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_counts}
    status_data = [
        status_dict.get('ACTIVE', 0),
        status_dict.get('USED', 0),
        status_dict.get('CANCELLED', 0) + status_dict.get('EXPIRED', 0)
    ]

    # Leaderboard: Top Stores by scans
    top_stores = Store.objects.annotate(
        scan_count=Count('vouchers__scans')
    ).order_by('-scan_count')[:5]

    context = {
        'total_stores': total_stores,
        'total_vouchers': total_vouchers,
        'used_vouchers': used_vouchers,
        'scans_today': scans_today,
        'revenue': total_rev,
        'pending_requests': pending_requests,
        'pending_store_requests': pending_store_requests,
        'scan_labels': scan_labels,
        'scan_counts': scan_counts,
        'status_data': status_data,
        'stores': Store.objects.all().order_by('-created_at')[:5],
        'top_stores': top_stores,
        'recent_scans': VoucherScan.objects.select_related(
            'voucher__store', 'scanned_by'
        ).order_by('-scanned_at')[:10],
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
def admin_user_list(request):
    if not request.user.is_admin():
        return redirect('dashboard')

    users = User.objects.order_by('role', 'username')
    return render(request, 'accounts/admin_user_list.html', {
        'users': users,
    })


@login_required
def admin_account_settings(request):
    if not request.user.is_admin():
        return redirect('dashboard')

    # Determine which form was submitted
    submitted_tab = request.POST.get('submitted_tab', 'profile')

    # Profile form
    profile_form = AccountSettingsForm(
        request.POST if request.method == 'POST' and submitted_tab == 'profile' else None,
        instance=request.user
    )
    if request.method == 'POST' and submitted_tab == 'profile' and profile_form.is_valid():
        profile_form.save()
        messages.success(request, 'Paramètres du compte mis à jour.')
        return redirect('/dashboard/admin/settings/?tab=profile')

    # Terms form
    term, _ = SitePolicy.objects.get_or_create(
        slug='terms-and-conditions',
        defaults={
            'title': 'Conditions Générales',
            'content': 'Entrez ici les conditions générales de votre service.',
        }
    )
    terms_form = TermsForm(
        request.POST if request.method == 'POST' and submitted_tab == 'terms' else None,
        instance=term
    )
    if request.method == 'POST' and submitted_tab == 'terms' and terms_form.is_valid():
        terms_form.save()
        messages.success(request, 'Conditions générales mises à jour.')
        return redirect('/dashboard/admin/settings/?tab=terms')

    # Add Pack form
    from apps.vouchers.forms import VoucherPriceForm
    pack_form = VoucherPriceForm(
        request.POST if request.method == 'POST' and submitted_tab == 'add_pack' else None
    )
    if request.method == 'POST' and submitted_tab == 'add_pack' and pack_form.is_valid():
        pack_form.save()
        messages.success(request, 'Pack de vouchers créé avec succès.')
        return redirect('/dashboard/admin/settings/?tab=packs')

    # Users list
    users = User.objects.order_by('role', 'username')

    # Fetch voucher packs
    from apps.vouchers.models import VoucherPrice
    packs = VoucherPrice.objects.order_by('price')

    active_tab = request.GET.get('tab', 'profile')
    if request.method == 'POST':
        active_tab = submitted_tab
        if active_tab == 'add_pack':
            active_tab = 'packs'

    return render(request, 'accounts/account_settings.html', {
        'form': profile_form,
        'terms_form': terms_form,
        'pack_form': pack_form,
        'term': term,
        'users': users,
        'packs': packs,
        'active_tab': active_tab,
    })


@login_required
def admin_terms_edit(request):
    if not request.user.is_admin():
        return redirect('dashboard')

    term, _ = SitePolicy.objects.get_or_create(
        slug='terms-and-conditions',
        defaults={
            'title': 'Conditions Générales',
            'content': 'Entrez ici les conditions générales de votre service.',
        }
    )
    form = TermsForm(request.POST or None, instance=term)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Conditions générales mises à jour.')
        return redirect('admin_terms_edit')

    return render(request, 'accounts/terms_edit.html', {'form': form, 'term': term})


@login_required
def manager_dashboard(request):
    if not request.user.is_manager():
        return redirect('dashboard')

    store = request.user.get_store()
    if not store:
        messages.warning(request, "Aucun magasin associé à votre compte.")
        return render(request, 'accounts/manager_dashboard.html', {'store': None})

    from apps.vouchers.models import Voucher, VoucherScan
    from django.db.models import Count
    from django.db.models.functions import TruncDay
    from datetime import timedelta

    today = timezone.now().date()
    vouchers_qs = store.vouchers.all()
    
    # Stats
    total_v = vouchers_qs.filter(status='BLANK').count()
    active_v = vouchers_qs.filter(status='ACTIVE').count()
    used_v = vouchers_qs.filter(status='USED').count()
    scans_t = VoucherScan.objects.filter(
        voucher__store=store, scanned_at__date=today
    ).count()

    # Cashier performance
    cashier_perf = store.caissiers.annotate(
        scan_count=Count('scans_performed')
    ).order_by('-scan_count')

    # Sum of active and used voucher values
    from django.db.models import Sum, F, Case, When, DecimalField
    from django.db.models.functions import Coalesce
    
    active_vouchers_amount = vouchers_qs.filter(status='ACTIVE').aggregate(total=Sum('value'))['total'] or 0
    
    # Consumed vouchers: sum of fully used + partially consumed amounts
    # Fully used: status='USED' sum their full value
    # Partially used: status='ACTIVE' sum (value - remaining_value)
    fully_used = vouchers_qs.filter(status='USED').aggregate(total=Sum('value'))['total'] or 0
    partially_consumed = vouchers_qs.filter(status='ACTIVE').annotate(
        consumed=F('value') - F('remaining_value')
    ).aggregate(total=Sum('consumed'))['total'] or 0
    used_vouchers_amount = fully_used + partially_consumed

    # Daily consumption (last 7 days activity)
    last_7d = timezone.now().date() - timedelta(days=6)
    daily_stats = VoucherScan.objects.filter(
        voucher__store=store,
        scanned_at__date__gte=last_7d
    ).annotate(day=TruncDay('scanned_at')).values('day').annotate(count=Count('id')).order_by('day')

    scan_labels = []
    scan_counts = []
    for i in range(7):
        d = last_7d + timedelta(days=i)
        scan_labels.append(d.strftime('%d %b'))
        count = next((item['count'] for item in daily_stats if item['day'].date() == d), 0)
        scan_counts.append(count)

    context = {
        'store': store,
        'vouchers': vouchers_qs.order_by('-created_at')[:10],
        'total_vouchers': total_v,
        'active_vouchers': active_v,
        'used_vouchers': used_v,
        'scans_today': scans_t,
        'caissiers': store.caissiers.all(),
        'cashier_perf': cashier_perf,
        'active_vouchers_amount': active_vouchers_amount,
        'used_vouchers_amount': used_vouchers_amount,
        'scan_labels': scan_labels,
        'scan_counts': scan_counts,
        'recent_scans': VoucherScan.objects.filter(
            voucher__store=store
        ).select_related('voucher', 'scanned_by').order_by('-scanned_at')[:10],
    }
    return render(request, 'accounts/manager_dashboard.html', context)


@login_required
def caissier_dashboard(request):
    if not request.user.is_caissier():
        return render_account_access_error(
            request,
            title="Accès réservé aux caissiers",
            message="Cette page est réservée aux caissiers. Votre compte magasin ne peut pas y accéder.",
        )

    store = request.user.get_store()

    from apps.vouchers.models import VoucherScan, Voucher
    today = timezone.now().date()

    activated_vouchers = Voucher.objects.filter(
        store=store,
        status__in=[Voucher.Status.ACTIVE, Voucher.Status.USED]
    ).order_by('-updated_at')

    context = {
        'store': store,
        'scans_today': VoucherScan.objects.filter(
            scanned_by=request.user, scanned_at__date=today
        ).count(),
        'activated_count': activated_vouchers.count(),
        'activated_amount': activated_vouchers.aggregate(total=Sum('value'))['total'] or 0,
        'activated_vouchers': activated_vouchers[:10],
        'recent_scans': VoucherScan.objects.filter(
            scanned_by=request.user
        ).select_related('voucher').order_by('-scanned_at')[:20],
    }
    return render(request, 'accounts/caissier_dashboard.html', context)


@login_required
def caissier_history(request):
    if not request.user.is_caissier():
        return render_account_access_error(
            request,
            title="Accès réservé aux caissiers",
            message="Cette page est réservée aux caissiers. Votre compte magasin ne peut pas y accéder.",
        )

    from apps.vouchers.models import Voucher, VoucherScan

    scans = VoucherScan.objects.filter(
        scanned_by=request.user
    ).select_related('voucher__store').order_by('-scanned_at')

    voucher_events = []
    for voucher in Voucher.objects.filter(updated_by=request.user).order_by('-updated_at'):
        if voucher.status == Voucher.Status.ACTIVE and voucher.remaining_value == voucher.value:
            action = 'Activé'
            amount = voucher.value
        elif voucher.status == Voucher.Status.ACTIVE and voucher.remaining_value < voucher.value:
            action = 'Consommé partiellement'
            amount = voucher.consumed_amount
        elif voucher.status == Voucher.Status.USED:
            action = 'Consommé'
            amount = voucher.consumed_amount
        else:
            action = 'Mise à jour'
            amount = voucher.value

        voucher_events.append({
            'type': action,
            'timestamp': voucher.updated_at,
            'voucher': voucher,
            'amount': amount,
            'remaining': voucher.remaining_value,
            'status': voucher.get_status_display(),
        })

    history_items = []
    for scan in scans:
        voucher = scan.voucher
        history_items.append({
            'type': 'Scan',
            'timestamp': scan.scanned_at,
            'voucher': voucher,
            'amount': voucher.value,
            'remaining': voucher.remaining_value,
            'status': voucher.get_status_display(),
            'note': scan.notes,
        })
    history_items.extend(voucher_events)
    history_items.sort(key=lambda item: item['timestamp'], reverse=True)

    return render(request, 'accounts/caissier_history.html', {
        'history_items': history_items,
    })


@login_required
def create_caissier(request):
    """Manager creates a caissier for his store."""
    if not request.user.is_manager():
        return render_account_access_error(
            request,
            title="Accès réservé aux managers",
            message="Vous ne pouvez pas créer de caissier avec ce type de compte.",
        )

    store = request.user.get_store()
    if not store:
        messages.error(request, "Vous n'avez pas de magasin associé.")
        return redirect('manager_dashboard')

    form = CaissierCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        caissier = form.save(commit=False)
        caissier.role = User.Role.CAISSIER
        caissier.set_password(form.cleaned_data['password'])
        caissier.save()
        store.caissiers.add(caissier)
        messages.success(request, f"Caissier '{caissier.username}' créé avec succès.")
        return redirect('manager_dashboard')

    return render(request, 'accounts/create_caissier.html', {'form': form, 'store': store})


@login_required
def delete_caissier(request, caissier_id):
    """Manager removes a caissier from his store."""
    if not request.user.is_manager():
        return render_account_access_error(
            request,
            title="Accès réservé aux managers",
            message="Vous ne pouvez pas supprimer un caissier avec ce type de compte.",
        )

    store = request.user.get_store()
    caissier = get_object_or_404(User, id=caissier_id, role=User.Role.CAISSIER)

    if request.method == 'POST':
        store.caissiers.remove(caissier)
        caissier.delete()
        messages.success(request, f"Caissier supprimé.")
    return redirect('caissier_list')


@login_required
def caissier_list(request):
    """Manager sees his store's caissiers."""
    if not request.user.is_manager():
        return render_account_access_error(
            request,
            title="Accès réservé aux managers",
            message="Vous ne pouvez pas accéder à la liste des caissiers avec ce type de compte.",
        )

    store = request.user.get_store()
    if not store:
        messages.error(request, "Aucun magasin associé.")
        return redirect('manager_dashboard')

    caissiers = store.caissiers.all().order_by('username')
    return render(request, 'accounts/caissier_list.html', {
        'caissiers': caissiers,
        'store': store
    })


@login_required
def edit_caissier(request, caissier_id):
    """Manager edits a caissier."""
    if not request.user.is_manager():
        return render_account_access_error(
            request,
            title="Accès réservé aux managers",
            message="Vous ne pouvez pas modifier ce caissier avec ce type de compte.",
        )

    store = request.user.get_store()
    caissier = get_object_or_404(User, id=caissier_id, role=User.Role.CAISSIER)

    # Security check: ensure this cashier belongs to the manager's store
    if not store.caissiers.filter(id=caissier_id).exists():
        messages.error(request, "Ce caissier ne appartient pas à votre magasin.")
        return redirect('caissier_list')

    from .forms import CaissierEditForm
    form = CaissierEditForm(request.POST or None, instance=caissier)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        new_password = form.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        user.save()
        messages.success(request, f"Profil de '{user.username}' mis à jour.")
        return redirect('caissier_list')

    return render(request, 'accounts/edit_caissier.html', {
        'form': form,
        'caissier': caissier
    })
