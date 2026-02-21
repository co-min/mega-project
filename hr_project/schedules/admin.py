from django.contrib import admin
from .models import Schedule
from .models import DayWorkPlan

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('employee', 'work_day', 'work_type', 'work_time')
    list_filter = ('work_day', 'work_type')

@admin.register(DayWorkPlan)
class DayWorkPlanAdmin(admin.ModelAdmin):
    list_display = ('employee', 'work_date', 'planned_start', 'planned_end')
    list_filter = ('work_date',)
