from django import forms
from .models import Ishchi, Lavozim, IshVaqti
from django.core.exceptions import ValidationError
from datetime import date

class IshchiSearchForm(forms.Form):
    ism = forms.CharField(max_length=100, required=False, label="Ism")
    familiya = forms.CharField(max_length=100, required=False, label="Familiya")
    lavozim = forms.ModelChoiceField(queryset=Lavozim.objects.all(), required=False, label="Lavozim", empty_label="Lavozim tanlang")


class BaseForm(forms.ModelForm):
    """Umumiy formalar uchun asosiy klass, takrorlanuvchi widgetlarni o'rnatish uchun"""
    def set_date_widget(self, field_name):
        return forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}, format='%Y-%m-%d')

    def set_time_widget(self, field_name):
        return forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'placeholder': 'HH:MM'})


class IshVaqtiForm(BaseForm):
    class Meta:
        model = IshVaqti
        fields = ['ishchi', 'kun', 'boshlanish_vaqti', 'tugash_vaqti']
        widgets = {
            'ishchi': forms.Select(attrs={'class': 'form-control'}),
        }

    kun = forms.DateField(widget=BaseForm().set_date_widget('kun'))
    boshlanish_vaqti = forms.TimeField(widget=BaseForm().set_time_widget('boshlanish_vaqti'))
    tugash_vaqti = forms.TimeField(widget=BaseForm().set_time_widget('tugash_vaqti'))


class LavozimForm(forms.ModelForm):
    class Meta:
        model = Lavozim
        fields = ['nomi']
        widgets = {
            'nomi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lavozim nomi'})
        }


class IshchiForm(forms.ModelForm):
    class Meta:
        model = Ishchi
        fields = ['ism', 'familiya', 'tugilgan_sana', 'jinsi', 'telefon', 'lavozim', 'ishga_kirgan_sana']

    tugilgan_sana = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        input_formats=['%Y-%m-%d'],
        required=True,
        label="Tug‘ilgan sana"
    )

    lavozim = forms.ModelChoiceField(queryset=Lavozim.objects.all(), required=True, empty_label="Lavozim tanlang", widget=forms.Select(attrs={'class': 'form-control'}))
    ism = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ism'}))
    familiya = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Familiya'}))
    telefon = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon raqami'}))

    # Telefon raqami validatsiyasi
    def clean_telefon(self):
        telefon = self.cleaned_data['telefon']
        if not telefon.isdigit():
            raise ValidationError('Telefon raqami faqat raqamlar bo‘lishi kerak.')
        if len(telefon) != 9:
            raise ValidationError('Telefon raqami 9 ta raqamdan iborat bo‘lishi kerak.')
        return telefon

    # Tug‘ilgan sana validatsiyasi
    def clean_tugilgan_sana(self):
        tugilgan_sana = self.cleaned_data['tugilgan_sana']
        if tugilgan_sana > date.today():
            raise ValidationError('Tug‘ilgan sana bugundan keyin bo‘lmasligi kerak.')
        return tugilgan_sana


def ishchi_create(request):
    if request.method == 'POST':
        form = IshchiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ishchilar_royxati')
    else:
        form = IshchiForm()
    return render(request, 'ishchilar/ishchi_form.html', {'form': form})