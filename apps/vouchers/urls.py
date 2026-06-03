from django.urls import path
from . import views

urlpatterns = [
    # Manager
    path('', views.voucher_list, name='voucher_list'),
    path('<int:pk>/', views.voucher_detail, name='voucher_detail'),
    path('<int:pk>/print/', views.voucher_print, name='voucher_print'),
    path('<int:pk>/fill/', views.voucher_fill, name='voucher_fill'),
    path('<int:pk>/redeem/', views.voucher_redeem, name='voucher_redeem'),
    path('requests/', views.voucher_request_list, name='voucher_request_list'),
    path('requests/create/', views.voucher_request_create, name='voucher_request_create'),

    # Admin
    path('admin/requests/', views.admin_request_list, name='admin_request_list'),
    path('admin/requests/<int:pk>/', views.admin_request_detail, name='admin_request_detail'),
    path('admin/requests/<int:pk>/approve/', views.admin_request_approve, name='admin_request_approve'),
    path('admin/requests/<int:pk>/reject/', views.admin_request_reject, name='admin_request_reject'),
    path('admin/packs/', views.pack_list, name='pack_list'),
    path('admin/packs/create/', views.pack_create, name='pack_create'),
    path('admin/packs/<int:pk>/edit/', views.pack_edit, name='pack_edit'),
]