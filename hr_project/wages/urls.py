from django.urls import path
from . import views

app_name = 'wages'

urlpatterns = [
    path('wages/', views.monthly_wage_view, name = 'wages'),
    path('check/', views.check_wage_view, name='check'),
]
