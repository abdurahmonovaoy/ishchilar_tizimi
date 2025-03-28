from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # ✅ Hamma viewlarni import qilishning eng to'g'ri yo'li
from .views import worklog_list, add_hodim, hodim_list, edit_hodim, delete_hodim, add_worklog, export_to_excel, hodim_detail, monthly_report, barcha_hodimlar, bugungi_keldi_kelmadi


app_name = 'hodimlar'

urlpatterns = [
    path('', views.barcha_hodimlar, name='barcha_hodimlar'),

    path('hodim_list/', views.hodim_list, name='hodim_list'),
    path("hodim/add/", views.add_hodim, name="add_hodim"),  # ✅ Hodim qo‘shish 
    path('add-hodim/', views.add_hodim, name='add_hodim'),  # ✅ To‘g‘ri URL nomi
    path("hodim/<int:id>/edit/", views.edit_hodim, name="edit_hodim"),  # ✅ Hodimni tahrirlash
    path("hodim/<int:id>/delete/", views.delete_hodim, name="delete_hodim"),
    path('hodim/<int:hodim_id>/', views.hodim_detail, name='hodim_detail'),
    path('barcha-hodimlar/', barcha_hodimlar, name='barcha_hodimlar'),
    path('bugungi-holati/', bugungi_keldi_kelmadi, name='bugungi_holati'),
   
    # path('add/', views.add_hodim, name='add_hodim'),  
    path('worklog/<int:hodim_id>/', views.add_worklog, name='add_worklog'), 
    path('worklogs/', worklog_list, name='worklog_list'),
    path("worklogs/export_excel/", views.export_to_excel, name="export_to_excel"),
    path("worklogs/export_pdf/", views.export_to_pdf, name="export_pdf"),
    path("worklogs/chart/", views.worklog_chart_data, name="worklog_chart_data"),
    path('worklog/<int:hodim_id>/', add_worklog, name='add_worklog'),  # hodim_id qo‘shildi 
    path('admin/monthly-report/', views.monthly_report, name='monthly_report'),
    path('monthly-work-hours/', views.monthly_work_hours, name='monthly_work_hours'),  # ✅ To'g'ri chaqirilgan
    path('report/', views.monthly_report, name='monthly_report'),  
    path('edit/<int:id>/', views.edit_hodim, name='edit_hodim'),
    path('delete/<int:id>/', views.delete_hodim, name='delete_hodim'),

    # Admin tizimga kirish
    path("admin_login/", views.admin_login, name="admin_login"),
    path("admin_logout/", views.admin_logout, name="admin_logout"),
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path('admin_dashboard/monthly_report/', views.monthly_report, name='monthly_report'),  # ✅ Shuni tekshiring!


    # Parolni unutganlar uchun reset sahifalari
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset_done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset_done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # path('hodimlar/', views.hodim_list, name='hodim_list'),
    # path("hodimlar/add/", views.add_hodim, name="add_hodim"),  
    path("hodimlar/<int:id>/edit/", views.edit_hodim, name="edit_hodim"),  
    path("hodimlar/<int:id>/delete/", views.delete_hodim, name="delete_hodim"),  
    path("hodimlar/<int:hodim_id>/add_worklog/", views.add_worklog, name="add_worklog"),  
    path("hodimlar/monthly_report/", views.monthly_report, name="monthly_report"),
    path('add_worklog/<int:hodim_id>/', add_worklog, name='add_worklog'),
    
    
    # path("export/excel/", export_to_excel, name="export_excel"),
    
]
