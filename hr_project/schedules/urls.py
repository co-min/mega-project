from django.urls import path
from . import views

app_name = 'schedules'

urlpatterns = [
    path('generate/<int:year>/<int:month>/', views.generate_monthly_schedule_view, name='generate'),
]