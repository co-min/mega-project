from django.db import models
from django.core.validators import MinValueValidator

#시급 관리
class Wage(models.Model):
  employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='wages')
  hourly_wage = models.IntegerField(validators=[MinValueValidator(0)])
  effective_start_date = models.DateField()

  class Meta:
    ordering =['-effective_start_date']

  def __str__(self):
    return f"{self.employee.full_name} - {self.hourly_wage}원 ({self.effective_start_date})"
