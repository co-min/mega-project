from django.contrib import admin
from .models import Wage

@admin.register(Wage)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('employee', 'hourly_wage')
