from django.contrib import admin
from .models import Ishchi, IshVaqti, IshHaqqi

@admin.register(Ishchi)
class IshchiAdmin(admin.ModelAdmin):
    list_display = ('ism', 'familiya', 'yosh', 'jinsi', 'lavozim', 'telefon', 'ishga_kirgan_sana')
    search_fields = ('ism', 'familiya', 'lavozim')
    list_filter = ('jinsi', 'lavozim', 'ishga_kirgan_sana')

@admin.register(IshVaqti)
class IshVaqtiAdmin(admin.ModelAdmin):
    list_display = ('ishchi', 'kun', 'boshlanish_vaqti', 'tugash_vaqti', 'ish_soati')

     # 'ish_soati' modeldagi metod bo'lgani uchun admin uchun moslashtiriladi
    def ish_soati(self, obj):
        return round(obj.ish_soati(), 2)  # 2 xonali aniqlik bilan
    ish_soati.short_description = 'Ishlangan soat'

@admin.register(IshHaqqi)
class IshHaqqiAdmin(admin.ModelAdmin):
    list_display = ('ishchi', 'oy', 'jami_ish_soati', 'tarif', 'jami_ish_haqi')
