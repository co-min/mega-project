from django.contrib import admin
from .models import Department, Shift, RoleSetting, MaxSetting, Employee, Event, Announcement, HiringSlot

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'days', 'time_range')
    list_filter = ('days',)

@admin.register(RoleSetting)
class RoleSettingAdmin(admin.ModelAdmin):
    list_display = ('role', 'base_wage', 'wage_type', 'increase_per_6_month')

@admin.register(MaxSetting)
class MaxSettingAdmin(admin.ModelAdmin):
    list_display = ('max_wage', 'min_wage')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'shift', 'phone', 'birth_year', 'role', 'wage')
    list_filter = ('department', 'shift', 'role')
    search_fields = ('full_name', 'phone')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'start', 'end', 'color', 'employee')
    list_filter = ('date', 'color')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'date')
    list_filter = ('date',)

@admin.register(HiringSlot)
class HiringSlotAdmin(admin.ModelAdmin):
    list_display = ('department', 'shift', 'status')
    list_filter = ('status', 'department', 'shift')
