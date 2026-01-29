from django.contrib import admin
from .models import Employee, Event, Announcement


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
    list_filter = ('is_active',)
    search_fields = ('full_name',)
