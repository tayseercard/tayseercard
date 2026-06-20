from django.db import models
from django.conf import settings
import uuid
import qrcode
from io import BytesIO
from django.core.files import File


class VoucherPrice(models.Model):
    """Admin-defined voucher price templates"""
    title = models.CharField(max_length=200, unique=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Valeur du voucher en DZD")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Prix de vente en DZD pour le pack")
    pack_quantity = models.PositiveIntegerField(default=1, help_text="Nombre de vouchers dans ce pack")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']
        verbose_name_plural = 'Voucher Packs & Prices'

    def __str__(self):
        return f"{self.title} ({self.price} DZD)"


class VoucherRequest(models.Model):
    """Store creates a request → Admin approves/rejects → QR generated"""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        APPROVED = 'APPROVED', 'Approuvé'
        REJECTED = 'REJECTED', 'Rejeté'

    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='voucher_requests',
    )
    price_template = models.ForeignKey(
        VoucherPrice,
        on_delete=models.PROTECT,
        related_name='requests',
        null=True, blank=True,
    )
    quantity = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    rejection_reason = models.TextField(blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='voucher_requests',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_requests',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    @property
    def title(self):
        return self.price_template.title

    @property
    def description(self):
        return self.price_template.description

    @property
    def value(self):
        return self.price_template.value

    @property
    def price(self):
        return self.price_template.price

    @property
    def total_amount(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.title} × {self.quantity} — {self.store.name} ({self.get_status_display()})"


class Voucher(models.Model):
    class Status(models.TextChoices):
        BLANK = 'BLANK', 'Vide'
        ACTIVE = 'ACTIVE', 'Actif'
        USED = 'USED', 'Consommé'
        EXPIRED = 'EXPIRED', 'Expiré'
        CANCELLED = 'CANCELLED', 'Annulé'

    request = models.ForeignKey(
        VoucherRequest,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vouchers',
    )
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='vouchers',
    )
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    qr_image = models.ImageField(upload_to='vouchers/qr/', blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True)
    beneficiary_name = models.CharField(max_length=200, blank=True)
    pin_code = models.CharField(max_length=10, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_vouchers',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_vouchers',
    )

    def generate_qr(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.code))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        self.qr_image.save(f'voucher_{self.code}.png', File(buffer), save=False)

    def save(self, *args, **kwargs):
        if not self.qr_image:
            self.generate_qr()
        super().save(*args, **kwargs)

    @property
    def consumed_amount(self):
        """Amount already consumed from this voucher."""
        if self.value is None or self.remaining_value is None:
            return 0
        return max(self.value - self.remaining_value, 0)

    def mark_as_used(self, scanned_by):
        self.status = self.Status.USED
        self.is_active = False
        self.save()

    def __str__(self):
        return f"{self.title} — {self.store.name} ({self.status})"


class VoucherScan(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='scans')
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='scans_performed',
    )
    scanned_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Scan {self.voucher.code} — {'✓' if self.is_valid else '✗'}"