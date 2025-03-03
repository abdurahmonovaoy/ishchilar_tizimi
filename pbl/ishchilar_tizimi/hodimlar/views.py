from django.shortcuts import render, redirect, get_object_or_404
from .models import hodim, WorkLog
from .forms import HodimForm, WorkLogForm
from django.contrib import messages
from django.db.models import Sum

def home_view(request):
    return render(request, "home.html")

# Hodim qo'shish
def add_hodim(request):
    if request.method == "POST":
        form = hodimForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Hodim muvaffaqiyatli qo'shildi!")
            return redirect('hodim_list')
    else:
        form = hodimForm()
    return render(request, 'hodimlar/add_hodim.html', {'form': form})

# Hodimlar ro'yxati va qidirish
def hodim_list(request):
    query = request.GET.get('q')
    hodimlar = hodim.objects.all()
    if query:
        hodimlar = hodimlar.filter(first_name__icontains=query) | hodimlar.filter(last_name__icontains=query)
    return render(request, 'hodimlar/hodim_list.html', {'hodimlar': hodimlar})

# Ish vaqtini qo'shish
def add_worklog(request, hodim_id):
    hodim = get_object_or_404(hodim, id=hodim_id)
    if request.method == "POST":
        form = WorkLogForm(request.POST)
        if form.is_valid():
            worklog = form.save(commit=False)
            worklog.hodim = hodim
            worklog.save()
            messages.success(request, "Ish vaqti muvaffaqiyatli qo'shildi!")
            return redirect('hodim_list')
    else:
        form = WorkLogForm()
    return render(request, 'hodimlar/add_worklog.html', {'form': form, 'hodim': hodim})

# Oy bo'yicha ishlagan soatlarni hisoblash
def monthly_report(request):
    hodimlar = hodim.objects.all()
    report = []
    for emp in hodimlar:
        total_hours = WorkLog.objects.filter(hodim=emp).aggregate(Sum('hours_worked'))['hours_worked__sum'] or 0
        report.append({'hodim': emp, 'total_hours': total_hours})
    return render(request, 'hodimlar/monthly_report.html', {'report': report})
