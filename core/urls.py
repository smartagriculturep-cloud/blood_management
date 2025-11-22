from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_page, name="logout"),
    path('', views.dashboard, name='dashboard'),
    path('donate', views.donate, name='donate'),
    path('donors/', views.donor_list, name='donor_list'),
    path('donors/add/', views.donor_create, name='donor_create'),
    path('donors/<int:pk>/edit/', views.donor_update, name='donor_update'),
    path('donors/<int:pk>/delete/', views.donor_delete, name='donor_delete'),

    path('inventory/', views.inventory_view, name='inventory'),

    path('donations/add/', views.donation_create, name='donation_create'),

    path('requests/', views.request_list, name='request_list'),
    path('requests/add/', views.request_create, name='request_create'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/<int:pk>/assign-donors/', views.assign_donors_to_request, name='assign_donors'),

    path('qr/patient/', views.patient_qr_view, name='patient_qr'),
    path('qr/donor/', views.donor_qr_view, name='donor_qr'),
    
    path('api/crossmatch/', views.crossmatch_api, name='crossmatch_api'),
]
