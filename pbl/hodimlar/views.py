import json
import logging
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
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from datetime import datetime, timedelta, time
from django.utils.timezone import localdate, now
from django.http import JsonResponse, HttpResponse
from datetime import date, timedelta, datetime
from django.utils.timezone import make_aware, get_current_timezone
from datetime import datetime, time
from .models import Hodim, WorkLog, AdminUser, LAVOZIMLAR
from .forms import HodimForm, HodimFormClean, WorkLogForm
from django.utils.timezone import localtime
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from collections import defaultdict
from django.core.cache import cache

# Audit logger for tracking important actions
audit_logger = logging.getLogger('audit')


# Store recent RFID scans in memory (for development)
# In production, you might want to use Redis or database
recent_rfid_scans = []


def bugungi_keldi_kelmadi(request):
    today = localdate()  # Bugungi sana

    # Bugun ishga kelgan hodimlarni olish
    ishga_kelgan_hodimlar = WorkLog.objects.filter(check_in__date=today).values_list('hodim_id', flat=True)

    # Hodimlar ro'yxati (newest first)
    barcha_hodimlar = Hodim.objects.all().order_by('-id')
    ishga_kelganlar = barcha_hodimlar.filter(id__in=ishga_kelgan_hodimlar)
    kelmaganlar = barcha_hodimlar.exclude(id__in=ishga_kelgan_hodimlar)

    # Statistics
    total_employees = Hodim.objects.count()
    present_today = ishga_kelganlar.count()
    absent_today = kelmaganlar.count()

    context = {
        'barcha_hodimlar': barcha_hodimlar,
        'ishga_kelganlar': ishga_kelganlar,
        'kelmaganlar': kelmaganlar,
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
    }
    return render(request, 'hodimlar/bugungi_holati.html', context)


def barcha_hodimlar(request):
    query = request.GET.get('q', '')  # Qidiruv so‘rovi
    today = date.today()  # Bugungi sana

    # Hodimlarni olish
    if query:
        hodimlar = (Hodim.objects.filter(first_name__icontains=query) | Hodim.objects.filter(last_name__icontains=query)).order_by('-id')
    else:
        hodimlar = Hodim.objects.all().order_by('-id')

    # Hodimlarning ish loglarini olish
    hodimlar_data = []
    for hodim in hodimlar:
        worklog = WorkLog.objects.filter(hodim=hodim, check_in__date=today).first()
        hodimlar_data.append({
            'first_name': hodim.first_name,
            'last_name': hodim.last_name,
            'check_in': worklog.check_in.strftime('%d/%m/%Y - %H:%M') if worklog and worklog.check_in else None,
            'check_out': worklog.check_out.strftime('%d/%m/%Y - %H:%M') if worklog and worklog.check_out else None,
        })

    return render(request, 'hodimlar/barcha_hodimlar.html', {
        'today': today,
        'query': query,
        'hodimlar_data': hodimlar_data
    })

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
            "check_in": log.check_in.strftime('%d/%m/%Y - %H:%M') if log.check_in else None,
            "check_out": log.check_out.strftime('%d/%m/%Y - %H:%M') if log.check_out else None,
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
            "check_in": log.check_in.strftime("%d/%m/%Y - %H:%M") if log else "-",
            "check_out": log.check_out.strftime("%d/%m/%Y - %H:%M") if log and log.check_out else "-",
            "hours_worked": log.hours_worked if log else 0
        })

        # ✅ To'g'ri log ma'lumotlarini yig'ish
        worklogs_data.append({
            'Ism': hodim.first_name,
            'Familiya': hodim.last_name,
            'Telefon': hodim.phone,
            'Lavozim': hodim.position,
            'Yoshi': hodim.age,
            'Kelgan vaqti': log.check_in.strftime("%d/%m/%Y - %H:%M") if log and log.check_in else "Ishga kelmagan",
            'Ketgan vaqti': log.check_out.strftime("%d/%m/%Y - %H:%M") if log and log.check_out else '-',
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

def worklog_list(request):
    """ Ish vaqtlari sahifasi (AJAX va filter qo'llangan) """
    query = request.GET.get("q", "").strip()
    date_filter = request.GET.get("date", "").strip()

    worklogs = WorkLog.objects.select_related("hodim").all().order_by('-check_in')
    # Order employees by most recently added first
    hodimlar = Hodim.objects.all().order_by('-id')

    # Qidirish bo'yicha filtr (supports partial and full name search)
    if query:
        query_parts = query.split()
        if len(query_parts) >= 2:
            # Full name search: "Ism Familiya"
            worklogs = worklogs.filter(
                Q(hodim__first_name__icontains=query_parts[0], hodim__last_name__icontains=query_parts[1]) |
                Q(hodim__first_name__icontains=query_parts[1], hodim__last_name__icontains=query_parts[0]) |
                Q(hodim__first_name__icontains=query) |
                Q(hodim__last_name__icontains=query)
            )
        else:
            # Single word search
            worklogs = worklogs.filter(
                Q(hodim__first_name__icontains=query) |
                Q(hodim__last_name__icontains=query)
            )
    
    # Sanaga qarab filtr
    if date_filter:
        try:
            date_obj = datetime.strptime(date_filter, "%Y-%m-%d").date()
            worklogs = worklogs.filter(check_in__date=date_obj)
        except ValueError:
            pass  # Noto‘g‘ri sana formati kiritilgan bo‘lsa, hech narsa qilmaymiz
    
    return render(request, "hodimlar/worklog_list.html", {
        "worklogs": worklogs,
        "hodimlar": hodimlar,
        "query": query,
        "date": date_filter,
        "today": localdate().strftime("%Y-%m-%d"),
    })


def monthly_work_hours(request):
    """Hodimlarning joriy oydagi ishlagan soatlarini hisoblash"""
    today = datetime.today()
    year, month = today.year, today.month

    hodimlar = Hodim.objects.all().order_by('-id')
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
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        # Rate limiting: Check for too many failed attempts
        client_ip = get_client_ip(request)
        cache_key = f"login_attempts_{client_ip}"
        attempts = cache.get(cache_key, 0)

        if attempts >= 5:
            # Audit log: Rate limit hit
            audit_logger.warning(f"LOGIN_RATE_LIMITED: IP {client_ip} blocked after {attempts} failed attempts")
            messages.error(request, "Juda ko'p noto'g'ri urinish! 15 daqiqa kutib turing.")
            return render(request, "admin/admin_login.html")

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            # Reset failed attempts on successful login
            cache.delete(cache_key)
            login(request, user)

            # Audit log: Successful login
            audit_logger.info(f"LOGIN_SUCCESS: User {username} logged in from IP {client_ip}")
            return redirect("hodimlar:admin_dashboard")
        else:
            # Increment failed attempts (expires in 15 minutes)
            cache.set(cache_key, attempts + 1, 900)

            # Audit log: Failed login
            audit_logger.warning(f"LOGIN_FAILED: Username '{username}' from IP {client_ip} (Attempt {attempts + 1})")
            messages.error(request, "Foydalanuvchi yoki parol noto'g'ri!")

    return render(request, "admin/admin_login.html")


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

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

    # ✅ Spreadsheet uchun bugungi barcha workloglar
    today_worklogs = WorkLog.objects.filter(check_in__date=today).select_related('hodim').order_by('-check_in')

    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'employee_names': employee_names,
        'work_hours': work_hours,
        'today_worklogs': today_worklogs,  # ✅ Spreadsheet uchun ma'lumot
    }
    return render(request, 'admin/admin_dashboard.html', context)
    

def admin_logout(request):
    logout(request)
    return redirect("hodimlar:admin_login")

# ✅ Google Sheets API Views
from .google_sheets_service import GoogleSheetsService
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import os

@csrf_exempt
def google_sheets_sync(request):
    """Sync all worklog data to Google Sheets"""
    if request.method == 'POST':
        try:
            # Get all worklogs (not just today)
            all_worklogs = WorkLog.objects.all().select_related('hodim').order_by('check_in')
            
            # Get spreadsheet ID from request if provided
            data = json.loads(request.body) if request.body else {}
            spreadsheet_id = data.get('spreadsheet_id')
            
            # Initialize Google Sheets service
            sheets_service = GoogleSheetsService()
            
            # Sync data
            result = sheets_service.sync_worklog_data(all_worklogs, spreadsheet_id)
            
            if result:
                return JsonResponse({
                    'status': 'success',
                    'message': f"{result['rows_updated']} qator yangilandi",
                    'spreadsheet_id': result['spreadsheet_id'],
                    'spreadsheet_url': result['url']
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Google Sheets bilan syncing amalga oshmadi'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Xatolik yuz berdi: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'POST method kerak'})

@csrf_exempt
def google_sheets_create(request):
    """Create new Google Spreadsheet"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
            title = data.get('title', 'Hodimlar Ish Vaqti')
            
            sheets_service = GoogleSheetsService()
            result = sheets_service.create_spreadsheet(title)
            
            if result:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Yangi Google Sheets yaratildi',
                    'spreadsheet_id': result['spreadsheet_id'],
                    'spreadsheet_url': result['url']
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Google Sheets yaratishda xatolik'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Xatolik: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'POST method kerak'})

def google_sheets_read(request, spreadsheet_id):
    """Read data from Google Spreadsheet"""
    try:
        sheets_service = GoogleSheetsService()
        data = sheets_service.read_data_from_sheet(spreadsheet_id)
        
        if data is not None:
            return JsonResponse({
                'status': 'success',
                'data': data,
                'rows_count': len(data)
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Google Sheets-dan ma\'lumot o\'qishda xatolik'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Xatolik: {str(e)}'
        })

@login_required 
def google_sheets_append(request):
    """Append new data to Google Spreadsheet"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            spreadsheet_id = data.get('spreadsheet_id')
            new_data = data.get('data', [])
            
            if not spreadsheet_id or not new_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'spreadsheet_id va data kerak'
                })
            
            sheets_service = GoogleSheetsService()
            success = sheets_service.append_data_to_sheet(spreadsheet_id, new_data)
            
            if success:
                return JsonResponse({
                    'status': 'success',
                    'message': f'{len(new_data)} qator qo\'shildi'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Ma\'lumot qo\'shishda xatolik'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Xatolik: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'POST method kerak'})

def google_sheets_settings(request):
    """Google Sheets credentials settings page"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            credentials_json = data.get('credentials_json', '').strip()
            
            if not credentials_json:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Credentials JSON matnini kiriting'
                })
            
            # Test the credentials
            sheets_service = GoogleSheetsService(credentials_json)
            
            if sheets_service.service:
                # Save credentials to database (secure)
                from .models import GoogleSheetsSettings
                
                # Deactivate old settings
                GoogleSheetsSettings.objects.filter(is_active=True).update(is_active=False)
                
                # Create new active settings
                GoogleSheetsSettings.objects.create(
                    credentials_json=credentials_json,
                    is_active=True
                )
                
                # Also backup to file for backward compatibility
                credentials_path = os.path.join(settings.BASE_DIR, 'google_credentials.json')
                with open(credentials_path, 'w') as f:
                    f.write(credentials_json)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Google Sheets credentials muvaffaqiyatli sozlandi va xavfsiz saqlandi!'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Credentials noto\'g\'ri yoki API ulanish xatosi'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'JSON format noto\'g\'ri'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Xatolik: {str(e)}'
            })
    
    # GET request - show current status
    try:
        from .models import GoogleSheetsSettings
        db_settings = GoogleSheetsSettings.get_active_settings()
        has_credentials = db_settings and db_settings.credentials_json
        
        # Fallback to file if database is empty
        if not has_credentials:
            credentials_path = os.path.join(settings.BASE_DIR, 'google_credentials.json')
            has_credentials = os.path.exists(credentials_path)
        
        context = {
            'has_credentials': has_credentials,
            'credentials_file_exists': has_credentials
        }
        return render(request, 'admin/google_sheets_settings.html', context)
        
    except Exception as e:
        context = {
            'has_credentials': False,
            'error': str(e)
        }
        return render(request, 'admin/google_sheets_settings.html', context)

def home_view(request):
    hodimlar = Hodim.objects.all().order_by('-id')
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
        print("POST MA'LUMOTLAR:", request.POST)  # ✅ Ma'lumotlarni konsolga chiqaramiz

        form = HodimForm(request.POST)
        if form.is_valid():
            try:
                # Save the employee and get the instance
                new_hodim = form.save()

                # Audit log: Employee created
                user = request.user.username if request.user.is_authenticated else 'Anonymous'
                audit_logger.info(f"HODIM_CREATED: {new_hodim.first_name} {new_hodim.last_name} (ID: {new_hodim.id}) by {user}")

                # Create detailed success message with full employee info
                success_message = f"""
                ✅ <strong>Yangi hodim muvaffaqiyatli qo'shildi!</strong><br><br>
                <div class="card mt-2 mb-2">
                    <div class="card-body py-3">
                        <h6 class="card-title text-success mb-3">
                            <i class="bi bi-person-check"></i> Qo'shilgan hodim ma'lumotlari:
                        </h6>
                        <div class="row">
                            <div class="col-md-6">
                                <p class="mb-2"><strong>👤 Ismi:</strong> {new_hodim.first_name}</p>
                                <p class="mb-2"><strong>👥 Familiyasi:</strong> {new_hodim.last_name}</p>
                                <p class="mb-2"><strong>📞 Telefon:</strong> {new_hodim.phone_number}</p>
                            </div>
                            <div class="col-md-6">
                                <p class="mb-2"><strong>💼 Lavozimi:</strong> {new_hodim.get_lavozim_display()}</p>
                                <p class="mb-2"><strong>🎂 Tug'ilgan sana:</strong> {new_hodim.birth_date.strftime('%d.%m.%Y')}</p>
                                <p class="mb-2"><strong>🏷️ RFID Karta:</strong> {new_hodim.card_uid if new_hodim.card_uid else 'Biriktirilmagan'}</p>
                            </div>
                        </div>
                        <div class="text-center mt-3">
                            <small class="text-muted">
                                <i class="bi bi-clock"></i> Qo'shilgan vaqt: {timezone.now().strftime('%d.%m.%Y %H:%M')}
                            </small>
                        </div>
                    </div>
                </div>
                """
                
                messages.success(request, success_message)
                
                # ✅ Clear RFID scan history after successful save
                global recent_rfid_scans
                recent_rfid_scans = []
                print("✅ Scan history cleared after successful employee creation")
                
                # Create a fresh form to clear all fields and errors (no initial values)
                form = HodimFormClean()
            except Exception as e:
                messages.error(request, f"❌ Xatolik: {str(e)}")
                print("Xatolik:", e)  # ✅ Xatolikni konsolga chiqaramiz
        else:
            messages.error(request, "❌ Xatolik bor! Iltimos, ma'lumotlarni tekshiring.")
            print("Form Xatolari:", form.errors)  # ✅ Formani xatolarini konsolga chiqaramiz

    else:
        form = HodimForm()

    return render(request, 'hodimlar/add_hodim.html', {
        'form': form,
        'LAVOZIMLAR': LAVOZIMLAR  # ✅ Endi xato chiqmaydi
    })


def hodim_list(request):
    query = request.GET.get('q', '').strip()
    # Order by most recently added first (newest first)
    hodimlar = Hodim.objects.all().order_by('-id')

    if query:
        # `Q` obyekti yordamida bir nechta shartlarni birlashtirish
        hodimlar = hodimlar.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(lavozim__icontains=query)
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
    if request.user.is_staff:
        template_name = "hodimlar/monthly_report.html"
        base_template = "admin_base.html"
    else:
        return render(request, "403.html")

    today = date.today()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    total_days_in_month = last_day.day

    work_start = time(8, 0)
    work_end = time(17, 0)

    monthly_work_logs = WorkLog.objects.filter(check_in__date__range=[first_day, last_day])

    employee_names = []
    attended_days = []
    absent_days = []
    late_days = []
    on_time_days = []
    benefits = []

    for hodim in Hodim.objects.all().order_by('-id'):
        full_name = f"{hodim.first_name} {hodim.last_name}"
        work_logs = monthly_work_logs.filter(hodim=hodim)

        attended = 0
        absent = 0
        late = 0
        on_time = 0

        days_with_checkin = set()

        for log in work_logs:
            if log.check_in:
                log_date = log.check_in.date()
                if log_date not in days_with_checkin:
                    attended += 1
                    check_in_local = localtime(log.check_in)  # ✅ Naive emas, localized
                    check_in_time = check_in_local.time()  # ✅ UTC vaqtni lokal vaqtga o‘tkazish

                    if check_in_time > work_start:
                        late += 1
                    else:
                        on_time += 1
                    days_with_checkin.add(log_date)

        absent = total_days_in_month - len(days_with_checkin)
        benefit = round(100 - (absent * 100 / total_days_in_month), 2)

        employee_names.append(full_name)
        attended_days.append(attended)
        absent_days.append(absent)
        late_days.append(late)
        on_time_days.append(on_time)
        benefits.append(benefit)
    print(employee_names, attended_days)
    context = {
        "employee_names": json.dumps(employee_names),
        "attended_days": json.dumps(attended_days),
        "absent_days": json.dumps(absent_days),
        "late_comers": json.dumps(late_days),
        "on_time_days": json.dumps(on_time_days),
        "benefits": json.dumps(benefits),
        "month": today.strftime('%B %Y'),
        "base_template": base_template,
    }

    return render(request, template_name, context)



def edit_hodim(request, id):
    hodim = get_object_or_404(Hodim, id=id)
    if request.method == "POST":
        print("POST data:", request.POST)
        form = HodimForm(request.POST, instance=hodim)
        if form.is_valid():
            # Save the updated employee and get the instance
            updated_hodim = form.save()

            # Audit log: Employee updated
            user = request.user.username if request.user.is_authenticated else 'Anonymous'
            audit_logger.info(f"HODIM_UPDATED: {updated_hodim.first_name} {updated_hodim.last_name} (ID: {updated_hodim.id}) by {user}")

            # Create detailed success message with updated employee info
            success_message = f"""
            ✅ <strong>Hodim ma'lumotlari muvaffaqiyatli yangilandi!</strong><br><br>
            <div class="card mt-2 mb-2">
                <div class="card-body py-3">
                    <h6 class="card-title text-success mb-3">
                        <i class="bi bi-person-check"></i> Yangilangan hodim ma'lumotlari:
                    </h6>
                    <div class="row">
                        <div class="col-md-6">
                            <p class="mb-2"><strong>👤 Ismi:</strong> {updated_hodim.first_name}</p>
                            <p class="mb-2"><strong>👥 Familiyasi:</strong> {updated_hodim.last_name}</p>
                            <p class="mb-2"><strong>📞 Telefon:</strong> {updated_hodim.phone_number}</p>
                        </div>
                        <div class="col-md-6">
                            <p class="mb-2"><strong>💼 Lavozimi:</strong> {updated_hodim.get_lavozim_display()}</p>
                            <p class="mb-2"><strong>🎂 Tug'ilgan sana:</strong> {updated_hodim.birth_date.strftime('%d.%m.%Y')}</p>
                            <p class="mb-2"><strong>🏷️ RFID Karta:</strong> {updated_hodim.card_uid if updated_hodim.card_uid else 'Biriktirilmagan'}</p>
                        </div>
                    </div>
                    <div class="text-center mt-3">
                        <small class="text-muted">
                            <i class="bi bi-clock"></i> Yangilangan vaqt: {timezone.now().strftime('%d.%m.%Y %H:%M')}
                        </small>
                    </div>
                </div>
            </div>
            """
            
            messages.success(request, success_message)
            return redirect('hodimlar:hodim_list')  # Yangilangan ro'yxatni ko'rsatish
        else:
            print(form.errors)  # Xatoliklar haqida ma'lumot olish
            messages.error(request, "Formani to'g'ri to'ldirish kerak!")
    else:
        form = HodimForm(instance=hodim)

    return render(request, 'hodimlar/edit_hodim.html', {
        'form': form,
        'hodim': hodim,
        'LAVOZIMLAR': LAVOZIMLAR
    })


def delete_hodim(request, id):
    try:
        hodim = Hodim.objects.get(id=id)
        hodim_name = f"{hodim.first_name} {hodim.last_name}"
        hodim_id = hodim.id
        hodim.delete()

        # Audit log: Employee deleted
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        audit_logger.info(f"HODIM_DELETED: {hodim_name} (ID: {hodim_id}) by {user}")

        messages.success(request, f"{hodim_name} o'chirildi!")
    except Hodim.DoesNotExist:
        messages.error(request, f"ID {id} bilan hodim topilmadi yoki allaqachon o'chirilgan!")
    
    return redirect('hodimlar:hodim_list')


# RFID API Endpoint
@csrf_exempt 
@require_http_methods(["GET"])
def get_recent_rfid_scans(request):
    """
    API endpoint to get recent RFID card scans for form auto-population
    Returns the most recent RFID card UIDs that have been scanned
    """
    try:
        global recent_rfid_scans
        # Check registration status for each scan
        scans_with_status = []
        for scan in recent_rfid_scans[:5]:
            scan_copy = scan.copy()
            # Check if card is registered
            is_registered = Hodim.objects.filter(card_uid=scan['card_uid']).exists()
            scan_copy['is_registered'] = is_registered
            if is_registered:
                hodim = Hodim.objects.get(card_uid=scan['card_uid'])
                scan_copy['employee_name'] = f"{hodim.first_name} {hodim.last_name}"
            else:
                scan_copy['employee_name'] = "Ro'yxatdan o'tmagan"
            scans_with_status.append(scan_copy)
            
        return JsonResponse({
            "status": "success",
            "recent_scans": scans_with_status,
            "count": len(recent_rfid_scans)
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Failed to get recent scans: {str(e)}"
        }, status=500)

@csrf_exempt 
@require_http_methods(["POST"])
def clear_rfid_scans(request):
    """
    API endpoint to clear recent RFID scan history
    """
    try:
        global recent_rfid_scans
        recent_rfid_scans = []
        return JsonResponse({
            "status": "success",
            "message": "Scan history cleared"
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Failed to clear scans: {str(e)}"
        }, status=500)

@csrf_exempt
@require_http_methods(["POST", "GET"])
def rfid_api(request):
    # Simple rate limiting - allow max 10 requests per minute per IP
    import time
    from collections import defaultdict
    
    if not hasattr(rfid_api, 'rate_limit'):
        rfid_api.rate_limit = defaultdict(list)
    
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', 
                request.META.get('REMOTE_ADDR', 'unknown'))
    current_time = time.time()
    
    # Clean old requests (older than 1 minute)
    rfid_api.rate_limit[client_ip] = [
        req_time for req_time in rfid_api.rate_limit[client_ip] 
        if current_time - req_time < 60
    ]
    
    # Check rate limit
    if len(rfid_api.rate_limit[client_ip]) >= 10:
        return JsonResponse({
            "status": "error", 
            "message": "Rate limit exceeded. Max 10 requests per minute."
        }, status=429)
    
    # Add current request time
    rfid_api.rate_limit[client_ip].append(current_time)
    
    """
    API endpoint to receive RFID data from Arduino ESP8266
    Handles both check-in and check-out based on existing logs
    """
    if request.method == "GET":
        return JsonResponse({"status": "ok", "message": "RFID API is running"})
    
    try:
        # Parse JSON data from request
        data = json.loads(request.body)
        
        # Extract data from Arduino payload
        card_uid = data.get('card_uid', '')
        values = data.get('values', '')
        gate_number = data.get('gate_number', 'Unknown')
        
        # Track recent RFID scan for form auto-population
        if card_uid:
            global recent_rfid_scans
            scan_data = {
                'card_uid': card_uid,
                'timestamp': timezone.now().isoformat(),
                'gate': gate_number
            }
            recent_rfid_scans.insert(0, scan_data)  # Add to beginning
            # Keep only last 10 scans
            recent_rfid_scans = recent_rfid_scans[:10]
        
        # Parse values (card_uid,student_id,first_name,last_name,phone,address,gate_number)
        values_list = values.split(',') if values else []
        
        if not card_uid:
            return JsonResponse({"status": "error", "message": "Card UID is required"})
        
        # Try to find existing employee by card UID
        hodim = None
        try:
            # PRIORITY 1: Find employee by assigned card UID in database
            hodim = Hodim.objects.get(card_uid=card_uid)
            print(f"✅ Found assigned employee: {hodim.first_name} {hodim.last_name} for card {card_uid}")
            
        except Hodim.DoesNotExist:
            # Don't auto-create employees anymore - just log unregistered card
            print(f"⚠️ Unregistered card scanned: {card_uid}")
            return JsonResponse({
                "status": "error", 
                "message": f"Ro'yxatdan o'tmagan karta: {card_uid}",
                "card_uid": card_uid,
                "action": "unregistered"
            })
        
        # Check today's work log
        today = localdate()
        current_time = now()
        
        # Find today's worklog for this employee
        today_log = WorkLog.objects.filter(
            hodim=hodim,
            check_in__date=today
        ).order_by('-check_in').first()
        
        if not today_log:
            # First scan of the day - CHECK IN
            worklog = WorkLog.objects.create(
                hodim=hodim,
                check_in=current_time
            )
            
            message = f"✅ Kelgan vaqti: {hodim.first_name} {hodim.last_name} - {localtime(current_time).strftime('%H:%M:%S')} ({gate_number})"
            
            return JsonResponse({
                "status": "success",
                "action": "check_in",
                "message": message,
                "employee": f"{hodim.first_name} {hodim.last_name}",
                "time": localtime(current_time).strftime('%H:%M:%S'),
                "gate": gate_number
            })
        
        elif not today_log.check_out:
            # Employee already checked in, now CHECK OUT
            today_log.check_out = current_time
            today_log.save()
            
            message = f"👋 Ketgan vaqti: {hodim.first_name} {hodim.last_name} - {localtime(current_time).strftime('%H:%M:%S')} ({gate_number})"
            
            # Calculate hours worked
            hours_worked = today_log.hours_worked
            
            return JsonResponse({
                "status": "success",
                "action": "check_out",
                "message": message,
                "employee": f"{hodim.first_name} {hodim.last_name}",
                "time": localtime(current_time).strftime('%H:%M:%S'),
                "gate": gate_number,
                "hours_worked": hours_worked
            })
        
        else:
            # Employee already checked in and out today - create new check-in
            worklog = WorkLog.objects.create(
                hodim=hodim,
                check_in=current_time
            )
            
            message = f"🔄 Qayta kelgan: {hodim.first_name} {hodim.last_name} - {localtime(current_time).strftime('%H:%M:%S')} ({gate_number})"
            
            return JsonResponse({
                "status": "success",
                "action": "re_check_in",
                "message": message,
                "employee": f"{hodim.first_name} {hodim.last_name}",
                "time": localtime(current_time).strftime('%H:%M:%S'),
                "gate": gate_number
            })
    
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON data"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})