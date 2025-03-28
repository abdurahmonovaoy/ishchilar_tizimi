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
from datetime import datetime, timedelta, time
from django.utils.timezone import localdate, now
from django.http import JsonResponse, HttpResponse
from datetime import date, timedelta, datetime
from django.utils.timezone import make_aware, get_current_timezone
from datetime import datetime, time


from .models import Hodim, WorkLog, AdminUser
from .forms import HodimForm, WorkLogForm


def bugungi_keldi_kelmadi(request):
    today = localdate()  # Bugungi sana
    
    # Bugun ishga kelgan hodimlarni olish
    ishga_kelgan_hodimlar = WorkLog.objects.filter(check_in__date=today).values_list('hodim_id', flat=True)
    
    # Hodimlar ro'yxati
    barcha_hodimlar = Hodim.objects.all()
    ishga_kelganlar = barcha_hodimlar.filter(id__in=ishga_kelgan_hodimlar)
    kelmaganlar = barcha_hodimlar.exclude(id__in=ishga_kelgan_hodimlar)

    context = {
        'ishga_kelganlar': ishga_kelganlar,
        'kelmaganlar': kelmaganlar
    }
    return render(request, 'hodimlar/bugungi_holati.html', context)


def barcha_hodimlar(request):
    hodimlar = Hodim.objects.all()
    return render(request, 'hodimlar/hodim_list.html', {'hodimlar': hodimlar})

def bugungi_hodimlar(request):
    today = localtime(now()).date()  # Bugungi sana
    query = request.GET.get("q", "").strip()

    # Bugun ishga kelgan hodimlarni olish
    work_logs = WorkLog.objects.filter(check_in__date=today)

    hodimlar_data = []
    for log in work_logs:
        hodimlar_data.append({
            "first_name": log.hodim.first_name,
            "last_name": log.hodim.last_name,
            "check_in": log.check_in.strftime('%H:%M') if log.check_in else None,
            "check_out": log.check_out.strftime('%H:%M') if log.check_out else None,
        })

    # Agar qidiruv bo'lsa
    if query:
        hodimlar_data = [h for h in hodimlar_data if query.lower() in h["first_name"].lower() or query.lower() in h["last_name"].lower()]

    return render(request, "hodimlar/bugungi_hodimlar.html", {
        "today": today,
        "hodimlar_data": hodimlar_data,
        "query": query,
    })

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
    if request.user.is_authenticated:  # Agar admin allaqachon tizimga kirgan bo'lsa
        return redirect('hodimlar:admin_dashboard')

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
    qidirish = request.GET.get('search', '').strip()
    filter_date = request.GET.get('date', '')

    if qidirish:
        worklogs = worklogs.filter(
            Q(hodim__first_name__icontains=qidirish) | Q(hodim__last_name__icontains=qidirish)
        )

    if filter_date:
        worklogs = worklogs.filter(check_in__date=filter_date)

    # ✅ Konsolga chiqishlar oldin bajariladi
    for log in worklogs:
        print(f"Hodim: {log.hodim.first_name} {log.hodim.last_name}, Kechikish: {log.late_check_in_hours}, Erta ketish: {log.early_leave_hours}")

    return render(request, 'hodimlar/worklog_list.html', {
        'worklogs': worklogs,
        'hodimlar': hodimlar
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
    query = request.GET.get('q', '').strip()
    hodimlar = Hodim.objects.all()

    if query:
        hodimlar = hodimlar.filter(
            first_name__icontains=query
        ) | hodimlar.filter(
            last_name__icontains=query
        ) | hodimlar.filter(
            lavozim__icontains=query
        )

    context = {
        'hodimlar': hodimlar,
        'query': query
    }
    return render(request, 'hodimlar/hodim_list.html', context)

def add_worklog(request, hodim_id):
    """Hodimning ish vaqtini qo‘shish va jami ishlagan vaqtini hisoblash"""
    hodim = get_object_or_404(Hodim, id=hodim_id)
    today = localdate()  # ✅ Bugungi sana

    # ✅ Bugungi oxirgi ish vaqti (agar mavjud bo‘lsa)
    last_worklog = WorkLog.objects.filter(hodim=hodim, check_in__date=today).order_by('-check_in').first()

    if request.method == "POST":
        check_in_str = request.POST.get("check_in")
        check_out_str = request.POST.get("check_out")

        if check_in_str:
            check_in = datetime.strptime(check_in_str, "%H:%M").time()
            check_in = datetime.combine(today, check_in)
            check_in = make_aware(check_in, get_current_timezone())
        else:
            check_in = None

        if check_out_str:
            check_out = datetime.strptime(check_out_str, "%H:%M").time()
            check_out = datetime.combine(today, check_out)
            check_out = make_aware(check_out, get_current_timezone())
        else:
            check_out = None  

        # ✅ Agar hodim bugun kelgan va ketmagan bo‘lsa, faqat ketish vaqtini yangilaymiz
        if last_worklog and not last_worklog.check_out:
            if check_out:
                if check_out <= last_worklog.check_in:
                    messages.error(request, "❌ Ketish vaqti kirish vaqtidan oldin bo‘lishi mumkin emas!")
                else:
                    last_worklog.check_out = check_out
                    last_worklog.save()
                    messages.success(request, "✅ Ketish vaqti muvaffaqiyatli qo‘shildi.")
            else:
                messages.error(request, "❌ Ketish vaqtini kiritish shart.")
        
        else:
            # ✅ Yangi ish vaqti kiritish
            if check_in:
                last_exit_time = WorkLog.objects.filter(
                    hodim=hodim, check_out__isnull=False, check_out__date=today
                ).order_by('-check_out').first()
                
                if last_exit_time and check_in <= last_exit_time.check_out:
                    messages.error(request, f"❌ Yangi kirish vaqti oxirgi chiqish vaqtidan ({last_exit_time.check_out.strftime('%H:%M')}) oldin bo‘lishi mumkin emas!")
                else:
                    new_worklog = WorkLog(hodim=hodim, check_in=check_in)
                    if check_out:
                        new_worklog.check_out = check_out
                    new_worklog.save()
                    messages.success(request, "✅ Yangi ish vaqti muvaffaqiyatli qo‘shildi.")
            else:
                messages.error(request, "❌ Kirish vaqtini kiritish shart!")

        return redirect('hodimlar:add_worklog', hodim_id=hodim.id)

    # ✅ Bugungi ish vaqtlari
    worklogs = WorkLog.objects.filter(hodim=hodim, check_in__date=today)

     # ✅ Jami ishlagan vaqtni HH:MM shaklida hisoblash
    total_seconds = sum(
        (log.check_out - log.check_in).total_seconds()
        for log in worklogs if log.check_out
    )
    total_hours = int(total_seconds // 3600)
    total_minutes = int((total_seconds % 3600) // 60)
    total_worked_time = f"{total_hours:02}:{total_minutes:02}"  # HH:MM format

    context = {
        "hodim": hodim,
        "worklogs": worklogs,
        "last_worklog": last_worklog,
        "total_worked_time": total_worked_time,
    }
    return render(request, "hodimlar/add_worklog.html", context)


def monthly_report(request):
    """ 🔹 Oylik ish vaqtlari va kechikish statistikasi """

    if request.user.is_staff:
        template_name = "admin/monthly_report.html"
        base_template = "admin_base.html"
    else:
        template_name = "hodimlar/monthly_report.html"
        base_template = "base.html"

    today = date.today()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    work_start = time(8, 0)  # Ish boshlanishi: 08:00
    work_end = time(17, 0)  # Ish tugashi: 17:00

    total_employees = Hodim.objects.count()
    today_work_logs = WorkLog.objects.filter(check_in__date=today)
    present_today = today_work_logs.count()
    absent_today = total_employees - present_today

    today_total_hours = sum(
        (log.check_out - log.check_in).total_seconds() / 3600
        for log in today_work_logs if log.check_out
    )
    today_avg_work_hours = round(today_total_hours / present_today, 2) if present_today else 0

    monthly_work_logs = WorkLog.objects.filter(check_in__date__range=[first_day, last_day])
    monthly_total_hours = sum(
        (log.check_out - log.check_in).total_seconds() / 3600
        for log in monthly_work_logs if log.check_out
    )
    monthly_avg_work_hours = round(monthly_total_hours / max(len(monthly_work_logs), 1), 2)

    # ✅ Hodimlar bo‘yicha ish vaqtlari va kechikish statistikasini hisoblash
    work_hours_data = {}
    late_days_data = {}  # Kechikish (soat)
    early_leave_data = {}  # Erta ketish (soat)
    absent_days_data = {}
    late_comers_data = {}  # Kech kelganlar (necha kun kechikkan)
    on_time_data = {}  # Vaqtida kelganlar (necha kun vaqtida kelgan)

    for hodim in Hodim.objects.all():
        work_logs = monthly_work_logs.filter(hodim=hodim)
        full_name = f"{hodim.first_name} {hodim.last_name}"

        total_work_seconds = 0
        total_late_seconds = 0
        total_early_leave_seconds = 0
        late_days = 0
        on_time_days = 0

        for log in work_logs:
            if log.check_in:
                check_in_time = log.check_in.time()
                check_out_time = log.check_out.time() if log.check_out else None

                # ⏳ **Kechikishni hisoblash (08:00 dan 1 soniya ham kechiksa kechikish hisoblanadi)**
                if check_in_time >= work_start:
                    total_late_seconds += (datetime.combine(date.min, check_in_time) - datetime.combine(date.min, work_start)).seconds
                    late_days += 1  # 🚀 **Necha kun kechikkanligini oshiramiz**
                else:
                    on_time_days += 1  # ✅ **Vaqtida kelgan kunlar sonini oshiramiz**

                # 🕒 **Erta ketishni hisoblash (17:00 dan oldin chiqsa hisoblash)**
                if check_out_time and check_out_time < work_end:
                    total_early_leave_seconds += (datetime.combine(date.min, work_end) - datetime.combine(date.min, check_out_time)).seconds

                # 🕘 **Ishlangan soatlarni hisoblash**
                if log.check_out:
                    total_work_seconds += (log.check_out - log.check_in).total_seconds()

        work_hours_data[full_name] = WorkLog.format_hours_minutes(None, total_work_seconds)
        late_days_data[full_name] = WorkLog.format_hours_minutes(None, total_late_seconds)
        early_leave_data[full_name] = WorkLog.format_hours_minutes(None, total_early_leave_seconds)
        absent_days_data[full_name] = last_day.day - len(work_logs)
        late_comers_data[full_name] = late_days  # ✅ **Necha kun kechikkan?**
        on_time_data[full_name] = on_time_days  # ✅ **Necha kun vaqtida kelgan?**

    context = {
        "total_employees": total_employees,
        "present_today": present_today,
        "absent_today": absent_today,
        "today_avg_work_hours": today_avg_work_hours,
        "monthly_avg_work_hours": monthly_avg_work_hours,
        "employee_names": json.dumps(list(work_hours_data.keys())),
        "work_hours": json.dumps(list(work_hours_data.values())),
        "late_days": json.dumps(list(late_days_data.values())),
        "on_time_days": json.dumps(list(on_time_data.values())),
        "absent_days": json.dumps(list(absent_days_data.values())),
        "late_comers": json.dumps(list(late_comers_data.values())),  # 🚀 **Kech kelgan kunlar soni**
        "month": today.strftime('%B %Y'),
        "base_template": base_template,
    }

    return render(request, template_name, context)


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