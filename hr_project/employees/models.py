from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Shift(models.Model):
    class Days(models.TextChoices):
        WEEKDAY_OPEN = 'weekday_open', _('평일 오픈')
        WEEKDAY_CLOSE = 'weekday_close', _('평일 마감')
        WEEKEND_OPEN = 'weekend_open', _('주말 오픈')
        WEEKEND_MIDDLE = 'weekend_middle', _('주말 미들')
        WEEKEND_CLOSE = 'weekend_close', _('주말 마감')

    name = models.CharField(max_length=50)
    days = models.CharField(max_length=20, choices=Days.choices)
    # e.g. "08:00-16:00"
    time_range = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.get_days_display()} · {self.time_range}"


class RoleSetting(models.Model):
    class WageType(models.TextChoices):
        HOURLY = 'hourly', _('시급')
        MONTHLY = 'monthly', _('월급')

    role = models.CharField(max_length=30, unique=True)
    base_wage = models.PositiveIntegerField(help_text=_('기본 급여'))
    wage_type = models.CharField(max_length=10, choices=WageType.choices, default=WageType.HOURLY)
    increase_per_6_month = models.PositiveIntegerField(default=0, help_text=_('6개월당 인상액'))

    def __str__(self):
        return self.role


class MaxSetting(models.Model):
    max_wage = models.PositiveIntegerField()
    min_wage = models.PositiveIntegerField()

    def __str__(self):
        return f"Max {self.max_wage} / Min {self.min_wage}"


phone_validator = RegexValidator(r'^010\d{8}$', _('전화번호는 010으로 시작하는 11자리여야 합니다.'))
color_validator = RegexValidator(r'^#(?:[0-9a-fA-F]{3}){1,2}$', _('유효한 HEX 색상이어야 합니다.'))
pin_validator = RegexValidator(r'^\d{4}$', _('출석 번호는 4자리 숫자여야 합니다.'))


class Employee(models.Model):
    full_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='employees/', blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employees')
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name='employees')
    phone = models.CharField(max_length=11, validators=[phone_validator])
    birth_year = models.PositiveIntegerField(validators=[MinValueValidator(1955), MaxValueValidator(2011)], help_text=_('출생년도'))
    favorite_color = models.CharField(max_length=7, validators=[color_validator], default='#2563eb')
    address = models.CharField(max_length=200)
    attendance_pin = models.CharField(max_length=4, validators=[pin_validator])

    class Role(models.TextChoices):
        PART_TIME = 'part_time', _('파트타임')
        MANAGER = 'manager', _('매니저')
        SUBSTITUTE = 'substitute', _('대체근무')

    class WageType(models.TextChoices):
        HOURLY = 'hourly', _('시급')
        MONTHLY = 'monthly', _('월급')

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PART_TIME)
    wage = models.PositiveIntegerField(default=0)
    wage_type = models.CharField(max_length=10, choices=WageType.choices, default=WageType.HOURLY)
    memo = models.TextField(blank=True)
    color_tag = models.CharField(max_length=7, validators=[color_validator], default='#22c55e')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class Event(models.Model):
    COLOR_CHOICES = (
        ('red', 'red'),
        ('blue', 'blue'),
        ('green', 'green'),
        ('purple', 'purple'),
        ('yellow', 'yellow'),
    )
    name = models.CharField(max_length=50)
    date = models.DateField()
    start = models.TimeField()
    end = models.TimeField()
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='blue')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')

    def __str__(self):
        return f"{self.name} {self.date} {self.start}-{self.end}"


class Announcement(models.Model):
    title = models.CharField(max_length=100)
    date = models.DateField()
    body = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} ({self.date})"


class HiringSlot(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT)

    class Status(models.TextChoices):
        OPEN = 'open', _('구인중')
        FILLED = 'filled', _('구인완료')

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    def __str__(self):
        return f"{self.department} · {self.shift} ({self.get_status_display()})"
