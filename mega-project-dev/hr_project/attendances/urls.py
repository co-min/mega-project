from django.urls import path
from . import views

app_name = 'attendances'
urlpatterns = [
    path('', views.attendance_view, name='attendances'),
    path('checkin_and_out/', views.attendance_checkin_and_out_view, name='checkin_and_out'),
    path('update/', views.admin_update_attendance_view, name='update'),
    path('break/', views.add_break_time_view, name ='break')
]