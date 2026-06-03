from django.urls import path
from . import views

urlpatterns = [
    path('', views.scan_page, name='scan_page'),
    path('validate/', views.validate_voucher, name='validate_voucher'),
    path('history/', views.scan_history, name='scan_history'),
]
