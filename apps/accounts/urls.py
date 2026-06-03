from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/settings/', views.admin_account_settings, name='admin_account_settings'),
    path('dashboard/admin/users/', views.admin_user_list, name='admin_user_list'),
    path('dashboard/admin/terms/', views.admin_terms_edit, name='admin_terms_edit'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/caissier/', views.caissier_dashboard, name='caissier_dashboard'),
    path('dashboard/caissier/history/', views.caissier_history, name='caissier_history'),
    path('caissiers/', views.caissier_list, name='caissier_list'),
    path('caissier/<int:caissier_id>/edit/', views.edit_caissier, name='edit_caissier'),
    path('caissier/create/', views.create_caissier, name='create_caissier'),
    path('caissier/<int:caissier_id>/delete/', views.delete_caissier, name='delete_caissier'),
]
