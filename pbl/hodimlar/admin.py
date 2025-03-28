from django.contrib import admin
from .models import Hodim, WorkLog, AdminUser
from .forms import WorkLogForm

# admin.site.site_header = "Ishchilar tizimi boshqaruv paneli"
# admin.site.site_title = "Ishchilar Tizimi"
# admin.site.index_title = "Boshqaruv paneli"


@admin.register(Hodim)
class HodimAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'lavozim', 'get_total_hours_worked')
    search_fields = ('first_name', 'last_name', 'phone_number')
    list_filter = ('is_active',)

    @admin.display(description="Umumiy Ishlagan Soatlar")
    def get_total_hours_worked(self, obj):
        return obj.total_hours_worked()



class WorkLogAdmin(admin.ModelAdmin):
    form = WorkLogForm
    list_display = ("hodim", "check_in", "check_out", "hours_worked_display", "late_check_in_display", "early_leave_display", "overtime_display")

    def hours_worked_display(self, obj):
        return f"{obj.hours_worked()} soat"
    hours_worked_display.short_description = "Ishlangan soat"

    def late_check_in_display(self, obj):  # To‘g‘ri metod nomi ishlatilmoqda
        return f"{obj.late_check_in_hours()} soat"
    late_check_in_display.short_description = "Kechikish (soat)"

    def early_leave_display(self, obj):
        return f"{obj.early_leave_hours()} soat"
    early_leave_display.short_description = "Oldin ketgan soat"

    def overtime_display(self, obj):
        return f"{obj.overtime_hours()} soat"
    overtime_display.short_description = "Ortiqcha ish (soat)"

admin.site.register(WorkLog, WorkLogAdmin)


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_admin')
    search_fields = ('username',)

# **Qo‘shimcha admin.site.register() KERAK EMAS, chunki @admin.register ishlatilgan!**

