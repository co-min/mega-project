from django.urls import path
from . import views

app_name = 'schedule'

urlpatterns = [
    path('generate/<int:year>/<int:month>/', views.generate_monthly_schedule_view, name='generate'),
    path('<int:employee_id>/', views.schedule_calendar_view, name='calendar'),
]
