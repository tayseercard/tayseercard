from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from apps.accounts.models import User
from .models import Store, StorePartnerRequest
from .forms import StoreSignupForm, StorePartnerRequestForm
from apps.vouchers.views import admin_required


@login_required
@admin_required
def store_list(request):
    stores = Store.objects.order_by('name')
    return render(request, 'stores/list.html', {'stores': stores})


def store_signup(request):
    form = StoreSignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        from django.db import transaction
        try:
            with transaction.atomic():
                manager = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['manager_first_name'],
                    last_name=form.cleaned_data['manager_last_name'],
                    role=User.Role.MANAGER,
                )
                manager.is_active = False
                manager.save()

                Store.objects.create(
                    manager=manager,
                    name=form.cleaned_data['store_name'],
                    address=form.cleaned_data.get('address', ''),
                    phone=form.cleaned_data.get('phone', ''),
                    description=form.cleaned_data.get('description', ''),
                    is_active=False,
                )

                StorePartnerRequest.objects.create(
                    first_name=form.cleaned_data['manager_first_name'],
                    last_name=form.cleaned_data['manager_last_name'],
                    store_name=form.cleaned_data['store_name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data.get('phone', ''),
                    status=StorePartnerRequest.Status.PENDING,
                )
            return render(request, 'stores/signup_pending.html')
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite lors de l'inscription : {str(e)}")

    return render(request, 'stores/signup.html', {'form': form})


@login_required
@admin_required
def store_request_list(request):
    requests_qs = StorePartnerRequest.objects.order_by('-created_at')
    return render(request, 'stores/request_list.html', {
        'requests': requests_qs,
    })


@login_required
@admin_required
def store_request_detail(request, pk):
    request_item = get_object_or_404(StorePartnerRequest, pk=pk)
    if request.method == 'POST' and request_item.status == StorePartnerRequest.Status.PENDING:
        from django.db import transaction
        manager = User.objects.filter(email__iexact=request_item.email).first()
        password = None
        email_sent = False

        try:
            with transaction.atomic():
                if manager:
                    manager.is_active = True
                    manager.save()
                    Store.objects.filter(manager=manager).update(is_active=True)
                else:
                    password = User.objects.make_random_password(length=10)
                    manager = User.objects.create_user(
                        username=request_item.email,
                        email=request_item.email,
                        password=password,
                        first_name=request_item.first_name,
                        last_name=request_item.last_name,
                        role=User.Role.MANAGER,
                    )
                    Store.objects.create(
                        manager=manager,
                        name=request_item.store_name,
                        phone=request_item.phone,
                        is_active=True,
                    )
                request_item.status = StorePartnerRequest.Status.APPROVED
                request_item.reviewed_at = timezone.now()
                request_item.reviewed_by = request.user
                request_item.save()

            # Send email
            from django.conf import settings
            from django.core.mail import send_mail
            from django.urls import reverse

            login_url = request.build_absolute_uri(reverse('login'))
            subject = "Activation de votre compte Tayseer Card"
            
            if password:
                message = (
                    f"Bonjour {request_item.first_name} {request_item.last_name},\n\n"
                    f"Votre demande de partenariat pour le magasin \"{request_item.store_name}\" a été approuvée par un administrateur.\n\n"
                    f"Voici vos accès pour vous connecter à la plateforme :\n"
                    f"- URL de connexion : {login_url}\n"
                    f"- E-mail de connexion : {request_item.email}\n"
                    f"- Mot de passe : {password}\n\n"
                    f"Pour des raisons de sécurité, nous vous recommandons de modifier votre mot de passe dès votre première connexion.\n\n"
                    f"Cordialement,\n"
                    f"L'équipe Tayseer Card"
                )
            else:
                message = (
                    f"Bonjour {request_item.first_name} {request_item.last_name},\n\n"
                    f"Votre demande de partenariat pour le magasin \"{request_item.store_name}\" a été approuvée par un administrateur.\n\n"
                    f"Votre compte est désormais actif. Vous pouvez vous connecter à la plateforme à l'adresse suivante :\n"
                    f"- URL de connexion : {login_url}\n"
                    f"- E-mail de connexion : {request_item.email}\n"
                    f"- Mot de passe : [Celui choisi lors de votre demande d'inscription]\n\n"
                    f"Cordialement,\n"
                    f"L'équipe Tayseer Card"
                )

            try:
                send_mail(
                    subject,
                    message,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@tayseercard.com'),
                    [request_item.email],
                    fail_silently=False,
                )
                email_sent = True
            except Exception:
                pass

            if password:
                if email_sent:
                    messages.success(request, f"Compte créé pour {manager.email} et accès envoyés par e-mail. Mot de passe : {password}")
                else:
                    messages.success(request, f"Compte créé pour {manager.email}. Mot de passe : {password} (L'envoi de l'e-mail a échoué, veuillez lui transmettre ces informations manuellement).")
            else:
                if email_sent:
                    messages.success(request, f"Le compte de {manager.email} a été activé et l'e-mail de confirmation a été envoyé.")
                else:
                    messages.success(request, f"Le compte de {manager.email} a été activé (l'envoi de l'e-mail de confirmation a échoué).")

        except Exception as e:
            messages.error(request, f"Une erreur s'est produite lors de l'approbation : {str(e)}")

        return redirect('store_request_detail', pk=request_item.pk)

    return render(request, 'stores/request_detail.html', {
        'request_item': request_item,
    })


@login_required
@admin_required
def store_delete(request, pk):
    store = get_object_or_404(Store, pk=pk)
    if request.method == 'POST':
        store_name = store.name
        # Delete the store. This will automatically delete all vouchers due to models.CASCADE.
        store.delete()
        messages.success(request, f"Le magasin '{store_name}' et tous ses vouchers associés ont été supprimés avec succès.")
    return redirect('store_list')


@login_required
@admin_required
def store_create(request):
    form = StoreSignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        from django.db import transaction
        try:
            with transaction.atomic():
                manager = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['manager_first_name'],
                    last_name=form.cleaned_data['manager_last_name'],
                    role=User.Role.MANAGER,
                )
                store = Store.objects.create(
                    manager=manager,
                    name=form.cleaned_data['store_name'],
                    address=form.cleaned_data.get('address', ''),
                    phone=form.cleaned_data.get('phone', ''),
                    description=form.cleaned_data.get('description', ''),
                    is_active=True,
                )
            messages.success(request, f"Le magasin '{store.name}' et son gérant '{manager.username}' ont été créés avec succès.")
            return redirect('store_list')
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite lors de la création : {str(e)}")

    return render(request, 'stores/add.html', {'form': form})

