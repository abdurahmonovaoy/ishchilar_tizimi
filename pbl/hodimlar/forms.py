from django import forms
from .models import Hodim, WorkLog, LAVOZIMLAR
from django.core.exceptions import ValidationError
from django.forms.widgets import DateTimeInput

class HodimForm(forms.ModelForm):
    lavozim = forms.ChoiceField(choices=LAVOZIMLAR, required=True)  # ✅ Lavozimni tanlash majburiy

    birth_date = forms.DateField(
        widget=forms.TextInput(attrs={'placeholder': 'DD.MM.YYYY', 'class': 'form-control'}),
        input_formats=['%d.%m.%Y']
    )

    class Meta:
        model = Hodim
        fields = ['first_name', 'last_name', 'birth_date', 'phone_number', 'lavozim']

class WorkLogForm(forms.ModelForm):
    check_in = forms.DateTimeField(
        widget=DateTimeInput(attrs={'type': 'datetime-local', 'class': 'vDateTimeField'}),
        input_formats=['%Y-%m-%d %H:%M', '%d.%m.%Y %H:%M']  # ✅ To‘g‘ri joylashgan
    )

    check_out = forms.DateTimeField(
        widget=DateTimeInput(attrs={'type': 'datetime-local', 'class': 'vDateTimeField'}),
        input_formats=['%Y-%m-%d %H:%M', '%d.%m.%Y %H:%M']  # ✅ To‘g‘ri joylashgan
    )

    class Meta:
        model = WorkLog
        fields = ['hodim', 'check_in', 'check_out']

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")

        if check_out and check_out < check_in:
            raise ValidationError("Tugash vaqti boshlanish vaqtidan oldin bo'lishi mumkin emas!")

        return cleaned_data