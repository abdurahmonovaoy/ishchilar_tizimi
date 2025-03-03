from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser, User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from datetime import timedelta

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

# Hodim modeli
class hodim(models.Model):  # Model nomini "hodim" qilib o'zgartirdik
    first_name = models.CharField(
        max_length=50,
        validators=[RegexValidator(r'^[a-zA-Z\s]+$', "Ism faqat harflardan iborat bo'lishi kerak")]
    )
    last_name = models.CharField(
        max_length=50,
        validators=[RegexValidator(r'^[a-zA-Z\s]+$', "Familiya faqat harflardan iborat bo'lishi kerak")]
    )
    age = models.PositiveIntegerField(validators=[MinValueValidator(18)])
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[RegexValidator(r'^\+998\d{9}$', "Telefon raqami +998 formatida va 9 ta raqamdan iborat bo'lishi kerak")]
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        unique_together = ('first_name', 'last_name', 'phone_number')

# Ish vaqti modeli
class WorkLog(models.Model):
    hodim = models.ForeignKey(hodim, on_delete=models.CASCADE)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.check_out and self.check_out < self.check_in:
            raise ValidationError(_('Tugash vaqti boshlanish vaqtidan oldin bo‘lishi mumkin emas.'))
        if self.check_out and (self.check_out - self.check_in) > timedelta(hours=24):
            raise ValidationError(_('Ish vaqti kuniga 24 soatdan oshmasligi kerak.'))

    def hours_worked(self):
        if self.check_out:
            worked_hours = (self.check_out - self.check_in).total_seconds() / 3600
            return min(worked_hours, 24)  # Maksimal 24 soat cheklovi
        return 0

    def __str__(self):
        return f"{self.hodim.first_name} {self.hodim.last_name} - {self.check_in} to {self.check_out}"


# class AdminUserProfile(models.Model):
#     user = models.OneToOneField(AdminUser, on_delete=models.CASCADE, related_name="profile")
    
#     def __str__(self):
#         return self.user.username

# Admin modeli (Alohida foydalanuvchilar uchun)
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