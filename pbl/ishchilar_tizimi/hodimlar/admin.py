from django.contrib import admin
from .models import hodim, WorkLog, AdminUser

# admin.site.site_header = "Ishchilar tizimi boshqaruv paneli"
# admin.site.site_title = "Ishchilar Tizimi"
# admin.site.index_title = "Boshqaruv paneli"

@admin.register(hodim)
class hodimAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'is_active')
    search_fields = ('first_name', 'last_name', 'phone_number')
    list_filter = ('is_active',)

    # # Admin paneldagi nomlarni o‘zbekchaga o‘zgartiramiz
    # def get_model_perms(self, request):
    #     perms = super().get_model_perms(request)
    #     perms['add'] = "Qo‘shish"
    #     perms['change'] = "O‘zgartirish"
    #     perms['delete'] = "O‘chirish"
    #     return perms

# admin.site.register(Hodim, HodimAdmin)

@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ('hodim', 'check_in', 'check_out', 'hours_worked')
    list_filter = ('hodim', 'check_in')

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_admin')
    search_fields = ('username',)

# **Qo‘shimcha admin.site.register() KERAK EMAS, chunki @admin.register ishlatilgan!**

