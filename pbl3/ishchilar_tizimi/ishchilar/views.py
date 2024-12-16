from django import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.timezone import now
from django.db.models import Sum, Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import datetime, time
from .models import Ishchi, IshHaqqi, Lavozim, IshVaqti
from .forms import IshchiForm, LavozimForm, IshVaqtiForm


# Lavozimlar ro'yxati
def lavozimlar_royxati(request):
    lavozimlar = Lavozim.objects.all()
    return render(request, 'ishchilar/lavozimlar_royxati.html', {'lavozimlar': lavozimlar})


# Lavozim qo'shish va yangilash
def lavozim_create_or_update(request, pk=None):
    lavozim = get_object_or_404(Lavozim, pk=pk) if pk else None
    if request.method == 'POST':
        form = LavozimForm(request.POST, instance=lavozim)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lavozim {'yangilandi' if pk else 'qo\'shildi'}.")
            return redirect('lavozimlar_royxati')
    else:
        form = LavozimForm(instance=lavozim)
    return render(request, 'ishchilar/lavozim_form.html', {'form': form})


# Lavozim o'chirish
def lavozim_delete(request, pk):
    lavozim = get_object_or_404(Lavozim, pk=pk)
    if request.method == 'POST':
        lavozim.delete()
        messages.success(request, 'Lavozim muvaffaqiyatli o\'chirildi.')
        return redirect('lavozimlar_royxati')
    return render(request, 'ishchilar/lavozim_confirm_delete.html', {'lavozim': lavozim})


# Ishchilar ro'yxati
def ishchilar_royxati(request):
    ishchilar = Ishchi.objects.all()
    ishchilar_haqida = [
        {
            'ishchi': ishchi,
            'jami_ish_soati': sum([vaqt.ish_soati() for vaqt in ishchi.ish_vaqtlari.all()]),
            'kechikkanlar': len([vaqt for vaqt in ishchi.ish_vaqtlari.all() if vaqt.boshlanish_vaqti > time(9, 0)]),
            'ishlagan_kunlar': len({vaqt.kun for vaqt in ishchi.ish_vaqtlari.all()}),
        }
        for ishchi in ishchilar
    ]
    return render(request, 'ishchilar/ishchilar_royxati.html', {'ishchilar_haqida': ishchilar_haqida})


# Ishchi qo'shish va yangilash
def ishchi_create_or_update(request, pk=None):
    ishchi = get_object_or_404(Ishchi, pk=pk) if pk else None
    if request.method == 'POST':
        form = IshchiForm(request.POST, instance=ishchi)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ishchi {'yangilandi' if pk else 'qo\'shildi'}.")
            return redirect('ishchilar_royxati')
    else:
        form = IshchiForm(instance=ishchi)
    return render(request, 'ishchilar/ishchi_form.html', {'form': form})


# Ishchi o'chirish
def ishchi_delete(request, pk):
    ishchi = get_object_or_404(Ishchi, pk=pk)
    if request.method == 'POST':
        ishchi.delete()
        messages.success(request, 'Ishchi muvaffaqiyatli o‘chirildi.')
        return redirect('ishchilar_royxati')
    return render(request, 'ishchilar/ishchi_confirm_delete.html', {'ishchi': ishchi})


# Ish vaqti qo'shish
def ish_vaqti_create(request):
    if request.method == 'POST':
        form = IshVaqtiForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ish vaqti muvaffaqiyatli qo\'shildi.')
            return redirect('ishchilar_royxati')
    else:
        form = IshVaqtiForm()
    return render(request, 'ishchilar/ish_vaqti_form.html', {'form': form})


# Ish haqi hisoblash
def ish_haqqi_hisoblash(request, ishchi_id):
    ishchi = get_object_or_404(Ishchi, id=ishchi_id)
    jami_ish_soati = sum([vaqt.ish_soati() for vaqt in ishchi.ish_vaqtlari.all()])
    tarif = 10_000  # Masalan, soatlik tarif
    jami_haqi = jami_ish_soati * tarif
    oy = datetime.now().strftime("%B")

    IshHaqqi.objects.update_or_create(
        ishchi=ishchi,
        oy=oy,
        defaults={
            'jami_ish_soati': jami_ish_soati,
            'tarif': tarif,
            'jami_ish_haqi': jami_haqi,
        }
    )
    return render(request, 'ishchilar/ish_haqqi.html', {'ishchi': ishchi, 'jami_haqi': jami_haqi})
