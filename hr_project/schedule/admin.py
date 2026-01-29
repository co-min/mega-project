from django.contrib import admin
from .models import Schedule
from .models import DayWorkPlan

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('employee', 'weekday', 'start_time', 'end_time')
    list_filter = ('weekday', 'is_active')

@admin.register(DayWorkPlan)
class DayWorkPlanAdmin(admin.ModelAdmin):
    list_display = ('employee', 'work_date', 'planned_start', 'planned_end')

"""
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'start', 'end', 'color', 'employee')
    list_filter = ('date', 'color')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'date')
    list_filter = ('date',)

"""