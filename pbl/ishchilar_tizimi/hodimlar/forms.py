from django import forms
from .models import hodim, WorkLog
from django.core.exceptions import ValidationError

class HodimForm(forms.ModelForm):
    class Meta:
        model = hodim
        fields = ['first_name', 'last_name', 'age', 'phone_number']

class WorkLogForm(forms.ModelForm):
    class Meta:
        model = WorkLog
        fields = ['hodim', 'check_in', 'check_out']

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")

        if check_out and check_out < check_in:
            raise ValidationError("Tugash vaqti boshlanish vaqtidan oldin bo'lishi mumkin emas")
