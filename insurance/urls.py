from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('get_quote/', views.get_quote, name='get_quote'),
    path('apply_insurance/', views.apply_insurance, name='apply_insurance'),
    path('inspections/', views.inspections, name='inspections'),
    path('submit_claim/', views.submit_claim, name='submit_claim'),
    path('policies/', views.view_policies, name='view_policies'),
    path('pay_policy/<int:policy_id>/', views.pay_policy, name='pay_policy'),
    path('renew_policy/<int:policy_id>/', views.renew_policy, name='renew_policy'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage_quotes/', views.manage_quotes, name='manage_quotes'),
    path('manage_applications/', views.manage_applications, name='manage_applications'),
    path('manage_inspections/', views.manage_inspections, name='manage_inspections'),
    path('manage_claims/', views.manage_claims, name='manage_claims'),
]