from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

color_validator = RegexValidator(r'^#(?:[0-9a-fA-F]{3}){1,2}$', _('유효한 HEX 색상이어야 합니다.'))
pin_validator = RegexValidator(r'^\d{4}$', _('출석 번호는 4자리 숫자여야 합니다.'))

# 직원
class Employee(models.Model):
    full_name = models.CharField(max_length=50)
    attendance_pin = models.CharField(max_length=4, validators=[pin_validator], unique=True)
    color_tag = models.CharField(max_length=7, validators=[color_validator], default='#22c55e')
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(null=True, blank=True)
    resign_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.full_name