import json
import pandas as pd
import datetime
import openpyxl
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import DurationField, ExpressionWrapper, Sum, F, Avg, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.views.decorators.csrf import csrf_protect
from .models import Hodim, WorkLog, AdminUser
from .forms import HodimForm, WorkLogForm
from datetime import datetime, timedelta
from django.utils.timezone import localdate
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from datetime import date, timedelta, datetime
# from reportlab.pdfgen import canvas


def hodim_detail(request, hodim_id):
    hodim = get_object_or_404(Hodim, id=hodim_id)
    today = datetime.today()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    worklogs = WorkLog.objects.filter(hodim=hodim, check_in__date__gte=first_day, check_in__date__lte=last_day)

    worklogs_data = []  # ✅ Bo‘sh ro‘yxat e’lon qilindi
    data = []
    for day in range(1, last_day.day + 1):
        date = first_day.replace(day=day)
        log = worklogs.filter(check_in__date=date).first()
        data.append({
            "day": day,
            "check_in": log.check_in.strftime("%H:%M") if log else "-",
            "check_out": log.check_out.strftime("%H:%M") if log and log.check_out else "-",
            "hours_worked": log.hours_worked if log else 0
        })

        # ✅ To'g'ri log ma'lumotlarini yig'ish
        worklogs_data.append({
            'Ism': hodim.first_name,
            'Familiya': hodim.last_name,
            'Telefon': hodim.phone,
            'Lavozim': hodim.position,
            'Yoshi': hodim.age,
            'Kelgan vaqti': log.check_in.strftime("%d.%m.%Y %H:%M") if log and log.check_in else "Ishga kelmagan",
            'Ketgan vaqti': log.check_out.strftime("%d.%m.%Y %H:%M") if log and log.check_out else '-',
            'Ishlangan soat': log.hours_worked if log else '-'
        })

    # ✅ Excel faylga yozish
    df = pd.DataFrame(worklogs_data)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="ishchilar_tizimi.xlsx"'
    df.to_excel(response, index=False)

    # ✅ HTML sahifaga ma'lumot qaytarish
    return render(request, 'hodimlar/hodim_detail.html', {
        'hodim': hodim,
        'worklogs': data
    })


# 📊 Kunlik statistikani hisoblash
def daily_statistics():
    today = now().date()
    total_employees = Hodim.objects.count()
    present_today = WorkLog.objects.filter(check_in__date=today).count()
    still_working = WorkLog.objects.filter(check_in__date=today, check_out__isnull=True).count()
    absent_today = total_employees - present_today

    return {
        "present_today": present_today,
        "still_working": still_working,
        "absent_today": absent_today,
    }

# 📈 Ish vaqtlarini JSON formatda qaytarish (Grafik uchun)
def worklog_chart_data(request):
    logs = WorkLog.objects.values("hodim__first_name", "hodim__last_name", "hours_worked")
    data = [
        {"hodim": f"{log['hodim__first_name']} {log['hodim__last_name']}", "hours": log["hours_worked"] or 0}
        for log in logs
    ]
    return JsonResponse(data, safe=False)

# 📥 Excel export qilish
def export_to_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="worklogs.csv"'
    writer = csv.writer(response)
    writer.writerow(["Hodim", "Check-in", "Check-out", "Worked Hours"])
    worklogs = WorkLog.objects.all()
    for worklog in worklogs:
        writer.writerow([
            worklog.hodim.first_name + " " + worklog.hodim.last_name,
            worklog.check_in_time,
            worklog.check_out_time,
            worklog.hours_worked()
        ])
    return response

def export_to_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="worklogs.pdf"'
    p = canvas.Canvas(response)
    y = 800
    p.drawString(100, y, "Hodim | Check-in | Check-out | Worked Hours")
    y -= 20
    worklogs = WorkLog.objects.all()
    for worklog in worklogs:
        p.drawString(100, y, f"{worklog.hodim.first_name} {worklog.hodim.last_name} | {worklog.check_in_time} | {worklog.check_out_time} | {worklog.hours_worked()}")
        y -= 20
    p.showPage()
    p.save()
    return response

# 📄 Ish vaqtlari sahifasi (AJAX va filter qo‘llangan)
def worklog_list(request):
    qidirish = request.GET.get("qidirish", "").strip()
    date_filter = request.GET.get("date", "").strip()
    
    worklogs = WorkLog.objects.select_related("hodim").all()
    if qidirish:
        worklogs = worklogs.filter(hodim__first_name__icontains=qidirish) | worklogs.filter(hodim__last_name__icontains=qidirish)
    if date_filter:
        worklogs = worklogs.filter(check_in__date=date_filter)

    hodimlar = Hodim.objects.all()
    statistics = daily_statistics()
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":  
        html = render_to_string("hodimlar/worklog_table.html", {"worklogs": worklogs, "hodimlar": hodimlar})
        return JsonResponse({"html": html})
    
    return render(request, "hodimlar/worklog_list.html", {"worklogs": worklogs, "hodimlar": hodimlar, "statistics": statistics})

def monthly_work_hours(request):
    """Hodimlarning joriy oydagi ishlagan soatlarini hisoblash"""
    today = datetime.today()
    year, month = today.year, today.month

    hodimlar = Hodim.objects.all()
    work_hours_data = []

    for hodim in hodimlar:
        worklogs = WorkLog.objects.filter(hodim=hodim, check_in__year=year, check_in__month=month)
        
        # ✅ Ishlangan soatlarni hisoblash
        total_hours = sum(log.hours_worked() for log in worklogs)

        work_hours_data.append({
            'hodim': hodim,
            'worked_hours': round(total_hours, 2)
        })

    context = {'work_hours_data': work_hours_data}
    return render(request, 'hodimlar/monthly_work_hours.html', context)


def admin_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect("hodimlar:admin_dashboard")
        else:
            messages.error(request, "Foydalanuvchi yoki parol noto‘g‘ri!")
    return render(request, "admin/admin_login.html")

@login_required
def admin_dashboard(request):
    today = now().date()  # ✅ Bugungi sana

    # Hodimlar statistikasi
    total_employees = Hodim.objects.count()
    present_today = WorkLog.objects.filter(check_in__date=today).values('hodim').distinct().count()
    absent_today = total_employees - present_today

    # ✅ Ishlangan soatlarni hisoblash
    worklogs = WorkLog.objects.filter(check_in__date=today).annotate(
        worked_hours=ExpressionWrapper(
            F('check_out') - F('check_in'),
            output_field=DurationField()
        )
    ).values('hodim__first_name', 'hodim__last_name', 'worked_hours')

    # 📊 Grafik uchun JSON ma'lumot
    employee_names = json.dumps([f"{log['hodim__first_name']} {log['hodim__last_name']}" for log in worklogs])
    work_hours = json.dumps([log['worked_hours'].total_seconds() / 3600 if log['worked_hours'] else 0 for log in worklogs])

    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'employee_names': employee_names,
        'work_hours': work_hours,
    }
    return render(request, 'admin/admin_dashboard.html', context)
    

def admin_logout(request):
    logout(request)
    return redirect("hodimlar:admin_login")

def worklog_list(request):
    """ Ish vaqtlarini chiqaruvchi sahifa """
    worklogs = WorkLog.objects.select_related("hodim").all()
    hodimlar = Hodim.objects.all()  # Hodimlar ro‘yxatini olish

    # Qidirish va filtrlash
    qidirish = request.GET.get('search', '').strip()  # ✅ To‘g‘ri 'search' o‘zgaruvchisi
    filter_date = request.GET.get('date', '')

    if qidirish:
        worklogs = worklogs.filter(
            Q(hodim__first_name__icontains=qidirish) | Q(hodim__last_name__icontains=qidirish)
        )

    if filter_date:
        worklogs = worklogs.filter(check_in__date=filter_date)

    return render(request, 'hodimlar/worklog_list.html', {
        'worklogs': worklogs,  # ✅ Lug‘at emas, to‘g‘ridan-to‘g‘ri QuerySet qaytarish
        'hodimlar': hodimlar  # Hodimlar ro‘yxatini HTMLga yuborish
    })


def home_view(request):
    hodimlar = Hodim.objects.all()
    work_logs = WorkLog.objects.all()
    admin_users = AdminUser.objects.all()

    for hodim in hodimlar:
        total_hours = WorkLog.objects.filter(hodim=hodim).aggregate(
            total=Sum(ExpressionWrapper(F('check_out') - F('check_in'), output_field=DurationField()))
        )['total']
        
        hodim.total_hours_in_month = round(total_hours.total_seconds() / 3600, 2) if total_hours else 0
        
        year, month = 2025, 3  # Mart oyi misol tariqasida
        hodim.present_days = hodim.days_present_in_month(year, month)
        hodim.absent_days = hodim.days_absent_in_month(year, month)
        hodim.late_days = hodim.days_late_in_month(year, month)

    context = {
        'hodimlar': hodimlar,
        'work_logs': work_logs,
        'admin_users': admin_users
    }
    
    return render(request, 'home.html', context)

def add_hodim(request):
    if request.method == "POST":
        form = HodimForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Hodim muvaffaqiyatli qo'shildi!")
            return redirect('hodimlar:hodim_list')
    else:
        form = HodimForm()
    return render(request, 'hodimlar/add_hodim.html', {'form': form})

def hodim_list(request):
    query = request.GET.get('q')
    hodimlar = Hodim.objects.all()
    if query:
        hodimlar = hodimlar.filter(first_name__icontains=query) | hodimlar.filter(last_name__icontains=query)
    return render(request, 'hodimlar/hodim_list.html', {'hodimlar': hodimlar})

def add_worklog(request, hodim_id):
    """Hodimning ish vaqtini qo‘shish"""
    hodim = get_object_or_404(Hodim, id=hodim_id)
    today = localdate()  # ✅ Bugungi sana

    if request.method == "POST":
        check_in_str = request.POST.get("check_in")
        check_out_str = request.POST.get("check_out")

        if check_in_str:
            check_in = datetime.strptime(check_in_str, "%H:%M").time()  
            check_in = datetime.combine(today, check_in)  # ✅ Bugungi sanaga bog‘lash
        else:
            check_in = None

        if check_out_str:
            check_out = datetime.strptime(check_out_str, "%H:%M").time()
            check_out = datetime.combine(today, check_out)  # ✅ Bugungi sanaga bog‘lash
        else:
            check_out = None  # ✅ Agar bo‘sh bo‘lsa, `None` saqlanadi

        if check_in:
            WorkLog.objects.create(hodim=hodim, check_in=check_in, check_out=check_out)  # ✅ Yangi ish vaqtini saqlash
            return redirect("hodimlar:add_worklog", hodim_id=hodim.id)

    # ✅ Bugungi ish vaqtlari
    worklogs = WorkLog.objects.filter(hodim=hodim, check_in__date=today)

    context = {
        "hodim": hodim,
        "worklogs": worklogs,
    }
    return render(request, "hodimlar/add_worklog.html", context)


def monthly_report(request):
    # Hodimlar sonini olish
    total_employees = Hodim.objects.count()

    # Bugungi sana
    today = datetime.today().date()

    # Bugun ishga kelgan hodimlar
    present_today = WorkLog.objects.filter(check_in__date=today).count()

    # Bugun kelmagan hodimlar
    absent_today = total_employees - present_today

    # Ishlagan soatlarni hisoblash
    work_logs = WorkLog.objects.all()
    work_hours = []
    employee_names = []

    for log in work_logs:
        if log.check_out:  # Agar chiqish vaqti mavjud bo‘lsa
            worked_seconds = (log.check_out - log.check_in).total_seconds()
            worked_hours = round(worked_seconds / 3600, 2)  # Sekundni soatga o‘girish
            work_hours.append(worked_hours)
            employee_names.append(f"{log.hodim.first_name} {log.hodim.last_name}")

    # O'rtacha ish soatini hisoblash
    avg_work_hours = round(sum(work_hours) / len(work_hours), 2) if work_hours else 0

    # 📊 Grafik uchun JSON format
    employee_names_json = json.dumps(employee_names)
    work_hours_json = json.dumps(work_hours)

    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'avg_work_hours': avg_work_hours,
        'employee_names': employee_names_json,
        'work_hours': work_hours_json,
    }

    return render(request, "admin/monthly_report.html", context)


def edit_hodim(request, id):
    hodim = get_object_or_404(Hodim, id=id)
    if request.method == "POST":
        form = HodimForm(request.POST, instance=hodim)
        if form.is_valid():
            form.save()
            messages.success(request, "Hodim ma'lumotlari yangilandi!")
            return redirect('hodimlar:hodim_list')  # ✅ TO‘G‘RI YO‘NALTIRISH
    else:
        form = HodimForm(instance=hodim)
    return render(request, 'hodimlar/edit_hodim.html', {'form': form, 'hodim': hodim})

def delete_hodim(request, id):
    hodim = get_object_or_404(Hodim, id=id)
    hodim.delete()
    messages.success(request, "Hodim o‘chirildi!")
    return redirect('hodimlar:hodim_list')  # ✅ TO‘G‘RI YO‘NALTIRISH