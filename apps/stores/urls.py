from django.urls import path
from . import views

urlpatterns = [
    path('', views.store_list, name='store_list'),
    path('signup/', views.store_signup, name='store_signup'),
    path('add/', views.store_create, name='store_create'),
    path('requests/', views.store_request_list, name='store_request_list'),
    path('requests/<int:pk>/', views.store_request_detail, name='store_request_detail'),
    path('<int:pk>/delete/', views.store_delete, name='store_delete'),
]