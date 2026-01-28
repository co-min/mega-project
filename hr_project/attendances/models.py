from django.db import models
from django.utils.translation import gettext_lazy as _
from employees.models import Employee


class AttendanceRecord(models.Model):
    """출퇴근 기록"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    
    class Status(models.TextChoices):
        WORKING = 'working', _('근무중')
        FINISHED = 'finished', _('퇴근')
        SICK_LEAVE = 'sick_leave', _('병가')
        VACATION = 'vacation', _('휴가')
        ABSENT = 'absent', _('결근')
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WORKING)
    memo = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date', '-check_in']
        unique_together = ['employee', 'date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"
