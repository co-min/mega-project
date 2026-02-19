from django.urls import path
from . import views

app_name = 'wages'

urlpatterns = [
    path('', views.monthly_wage_view, name='monthly'),
    path('change/<int:employee_id>/', views.change_hourly_wage_view, name='hourly_wage_change'),
    path('check/', views.check_wage_view, name='check'),
]
