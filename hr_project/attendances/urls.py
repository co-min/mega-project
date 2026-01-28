from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_view, name='attendance'),
    path('checkin/', views.attendance_checkin_view, name='attendance_checkin'),
    path('checkout/', views.attendance_checkout_view, name='attendance_checkout'),
]
