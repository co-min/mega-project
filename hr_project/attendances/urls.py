from django.urls import path
from . import views

app_name = 'attendances'
urlpatterns = [
    path('', views.attendance_view, name='attendances'),
    path('checkin/', views.attendance_checkin_view, name='checkin'),
    path('checkout/', views.attendance_checkout_view, name='checkout'),
    path('load/', views.day_attendance_view, name='daywork'),
    path('update/<int:attendance_id>/', views.admin_update_attendance_view, name='update')
]
