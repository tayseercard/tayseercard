from django.db import models
from django.conf import settings


class Store(models.Model):
    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='managed_store',
        limit_choices_to={'role': 'MANAGER'},
    )
    caissiers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='caissier_store',
        blank=True,
        limit_choices_to={'role': 'CAISSIER'},
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='stores/logos/', blank=True, null=True)
    address = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_vouchers(self):
        return self.vouchers.count()

    def active_vouchers(self):
        return self.vouchers.filter(is_active=True).count()

    def total_scans_today(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.vouchers.filter(
            scans__scanned_at__date=today
        ).count()


class StorePartnerRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        APPROVED = 'APPROVED', 'Accepté'
        REJECTED = 'REJECTED', 'Rejeté'

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    store_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_store_requests',
    )

    def __str__(self):
        return f"{self.store_name} — {self.email}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING
