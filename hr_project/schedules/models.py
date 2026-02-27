from django.db import models
from employees.models import Employee
from schedules.constants import WORK_TYPE, WEEKDAYS

# 근무 스케줄 템플릿
class Schedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    work_type = models.IntegerField(choices=WORK_TYPE)
    work_day = models.IntegerField(choices=WEEKDAYS)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default = True)

    def __str__(self):
        time_range = (
            f"{self.start_time.strftime('%H:%M')}~{self.end_time.strftime('%H:%M')}"
            if self.start_time and self.end_time
            else "-"
        )
        return f"{self.employee.full_name} {self.get_work_day_display()} {time_range}"


# monthly 근무 스케줄
class DayWorkPlan(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='dayworkplans')
    schedule = models.ForeignKey (Schedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='day_work_plans')
    work_date=models.DateField()
    planned_start = models.TimeField(null=True, blank=True)
    planned_end = models.TimeField(null=True, blank=True)

    def __str__(self):
        time_range = (
            f"{self.planned_start.strftime('%H:%M')}~{self.planned_end.strftime('%H:%M')}"
            if self.planned_start and self.planned_end
            else "-"
        )
        return f"{self.employee.full_name} {self.work_date} {time_range}"
