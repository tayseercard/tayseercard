from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user with 3 roles:
    - ADMIN: superuser / platform owner (your client)
    - MANAGER: store owner, creates vouchers & caissiers
    - CAISSIER: store employee, scans & validates QR codes
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur'
        MANAGER = 'MANAGER', 'Manager de magasin'
        CAISSIER = 'CAISSIER', 'Caissier'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MANAGER,
    )

    # Caissier is linked to a store through the store's manager
    # Manager is linked to a store via Store.manager FK

    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_manager(self):
        return self.role == self.Role.MANAGER

    def is_caissier(self):
        return self.role == self.Role.CAISSIER

    def get_store(self):
        """Returns the store associated with this user (manager or caissier)."""
        if self.is_manager():
            return getattr(self, 'managed_store', None)
        elif self.is_caissier():
            caissier_store = getattr(self, 'caissier_store', None)
            if hasattr(caissier_store, 'first'):
                return caissier_store.first()
            return caissier_store
        return None

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class SitePolicy(models.Model):
    """Editable site policy text like terms and conditions."""
    slug = models.SlugField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Politique du site'
        verbose_name_plural = 'Politiques du site'

    def __str__(self):
        return self.title
