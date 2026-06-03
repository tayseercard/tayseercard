from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from apps.accounts import views

# This loads our custom admin registrations
import tayseercard.admin_config  # ← add this line

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('stores/', include('apps.stores.urls')),
    path('vouchers/', include('apps.vouchers.urls')),
    path('manager/vouchers/', include('apps.vouchers.urls')),
    path('caissier/vouchers/', include('apps.vouchers.urls')),
    path('scan/', include('apps.scanning.urls')),
    path('', include('apps.accounts.urls')),
    path('', views.home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)