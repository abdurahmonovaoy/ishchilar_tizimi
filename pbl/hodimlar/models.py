from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from datetime import datetime, timedelta, date, time
from django.utils.timezone import localtime, make_aware, get_current_timezone, now
from django.contrib.auth.models import AbstractUser


class AdminUser(AbstractUser):
    is_admin = models.BooleanField(default=True)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="admin_users",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="admin_users_permissions",
        blank=True
    )

    def __str__(self):
        return self.username


# Telefon raqamini tekshirish uchun funksiya
def validate_phone_number(value):
    pattern = re.compile(r'^\+998\d{9}$')
    if not pattern.match(value):
        raise ValidationError(_('Noto‘g‘ri telefon raqam formati! +998XXXXXXXXX ko‘rinishida bo‘lishi kerak.'))

# Ism va familiyada maxsus belgilar yoki raqamlarni rad etish
def validate_name(value):
    if not value.isalpha():
        raise ValidationError(_('Ism va familiyada faqat harflar bo‘lishi kerak.'))

# Musbat yoshni tekshirish
def validate_age(value):
    if value < 18:
        raise ValidationError(_('Yosh 18 dan kichik bo‘lishi mumkin emas.'))

# Lavozimlar
def get_default_positions():
    return ['Direktor', 'Hisobchi', 'Dasturchi', 'Xodim']

LAVOZIMLAR = [
        ('Tikuvch', 'Tikuvchi'),
        ('Orta kesuv', 'Orta kesuv'),
        ('Kesuv', 'Kesuv'),
        ('Mehanik', 'Mehanik'),
        ('Ish bay', 'Ish bay'),
    ]

# Hodim modeli
class Hodim(models.Model):
    first_name = models.CharField(
        max_length=50,
        validators=[RegexValidator(r'^[a-zA-Z\s]+$', "Ism faqat harflardan iborat bo'lishi kerak")]
    )
    last_name = models.CharField(
        max_length=50,
        validators=[RegexValidator(r'^[a-zA-Z\s]+$', "Familiya faqat harflardan iborat bo'lishi kerak")]
    )
    # age = models.PositiveIntegerField(validators=[MinValueValidator(18)])
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[RegexValidator(r'^\+998\d{9}$', "Telefon raqami +998 formatida va 9 ta raqamdan iborat bo'lishi kerak")]
    )
    lavozim = models.CharField(
        max_length=50,
        choices=LAVOZIMLAR,
        default='Tikuvchi'  # Agar lavozim tanlanmasa, "Tikuvchi" deb belgilaydi
    )
    
     # ✅ Tug‘ilgan sana (DD.MM.YYYY formatida)
    birth_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_lavozim_display()}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['first_name', 'last_name', 'phone_number'],
                name='unique_hodim'
            )
        ]
        ordering = ['first_name', 'last_name']
        verbose_name = "Hodim"
        verbose_name_plural = "Hodimlar"

    def days_present_in_month(self, year, month):
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        return WorkLog.objects.filter(hodim=self, check_in__date__range=[first_day, last_day]).count()

    def days_absent_in_month(self, year, month):
        total_days = (datetime(year, month + 1, 1) - timedelta(days=1)).day
        return total_days - self.days_present_in_month(year, month)

    def days_late_in_month(self, year, month):
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        return WorkLog.objects.filter(hodim=self, check_in__date__range=[first_day, last_day], check_in__hour__gt=9).count()

    def total_hours_worked(self):
        """Hodimning umumiy ishlagan soatlarini hisoblash"""
        worklogs = WorkLog.objects.filter(hodim=self, check_out__isnull=False)
        return sum(log.hours_worked() for log in worklogs)

# Ish vaqti modeli
class WorkLog(models.Model):
    hodim = models.ForeignKey('Hodim', on_delete=models.CASCADE)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.check_out and self.check_out < self.check_in:
            raise ValidationError(_('Tugash vaqti boshlanish vaqtidan oldin bo‘lishi mumkin emas.'))
        if self.check_out and (self.check_out - self.check_in) > timedelta(hours=24):
            raise ValidationError(_('Ish vaqti kuniga 24 soatdan oshmasligi kerak.'))

    def hours_worked(self):
        """Ishlangan vaqtni HH:MM formatida qaytarish"""
        if self.check_out:
            total_seconds = (self.check_out - self.check_in).total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours:02}:{minutes:02}"  # HH:MM format
        return "00:00"

    def late_check_in_hours(self):  # ✅ Joy tashlash to‘g‘ri
        """Hodim 09:00 dan kechiksa, kechikish vaqtini qaytaradi (HH:MM formatida)."""
        if self.check_in and self.check_in.time() > time(9, 0):
            late_seconds = (self.check_in - self.check_in.replace(hour=9, minute=0, second=0)).total_seconds()
            return self.format_hours_minutes(late_seconds)
        return "00:00"

    def early_leave_hours(self):
        """Hodim 18:00 dan oldin chiqsa, erta ketish vaqtini qaytaradi (HH:MM formatida)."""
        if self.check_out and self.check_out.time() < time(18, 0):
            early_seconds = (self.check_out.replace(hour=18, minute=0, second=0) - self.check_out).total_seconds()
            return self.format_hours_minutes(early_seconds)
        return "00:00"

    def format_hours_minutes(self, total_seconds):
        """Sekundlarni HH:MM formatiga o‘zgartirish."""
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"{hours:02}:{minutes:02}"  # HH:MM format"

    def __str__(self):
        return f"{self.hodim} - {localtime(self.check_in)}"

    @property
    def worked_hours(self):
        if self.check_out:
            return round((self.check_out - self.check_in).total_seconds() / 3600, 2)
        return 0
