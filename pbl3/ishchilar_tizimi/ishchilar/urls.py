from django.urls import path
from . import views

urlpatterns = [
    # Bosh sahifa - Ishchilar ro'yxati
    path('', views.ishchilar_royxati, name='ishchilar_royxati'),
    path('ishchilar/', views.ishchilar_royxati, name='ishchilar_royxati'),

    # Ish vaqti
    path('ishchi/vaqt/', views.ish_vaqti_create, name='ish_vaqti_create'),

    # Ishchi CRUD operatsiyalari
    path('ishchi/yangi/', views.ishchi_create_or_update, name='ishchi_create'),
    path('ishchi/<int:pk>/yangilash/', views.ishchi_create_or_update, name='ishchi_update'),
    path('ishchi/<int:pk>/ochirish/', views.ishchi_delete, name='ishchi_delete'),
    path('ishchi/<int:ishchi_id>/', views.ishchi_hisoboti, name='ishchi_hisoboti'),

    # Lavozim CRUD operatsiyalari
    path('lavozimlar/', views.lavozimlar_royxati, name='lavozimlar_royxati'),
    path('lavozim/yangi/', views.lavozim_create_or_update, name='lavozim_create'),
    path('lavozim/<int:pk>/yangilash/', views.lavozim_create_or_update, name='lavozim_update'),
    path('lavozim/<int:pk>/ochirish/', views.lavozim_delete, name='lavozim_delete'),

    # Ish soati va ish haqi hisoblash
    path('ishchi/<int:ishchi_id>/ish_soati/', views.ish_soati_hisobla, name='ish_soati_hisobla'),
    path('ish_haqqi/<int:ishchi_id>/', views.ish_haqqi_hisoblash, name='ish_haqqi_hisoblash'),
]
