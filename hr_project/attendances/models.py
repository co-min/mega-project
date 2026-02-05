from django.db import models
from django.utils.translation import gettext_lazy as _
from employees.models import Employee

# 실제 출퇴근 기록
class AttendanceRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date', '-check_in']
        unique_together = ['employee', 'date']
        
    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"


# 근무 상태
class Status(models.TextChoices):
    PLANNED = 'planned', _('근무 예정')
    WORKING = 'working', _('근무중')
    FINISHED = 'finished', _('퇴근')
    ABSENT = 'absent', _('결근')


