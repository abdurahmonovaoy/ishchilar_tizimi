from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # ✅ Hamma viewlarni import qilishning eng to'g'ri yo'li
from .views import worklog_list, add_hodim, hodim_list, edit_hodim, delete_hodim, add_worklog, export_to_excel, hodim_detail, monthly_report, barcha_hodimlar, bugungi_keldi_kelmadi


app_name = 'hodimlar'

urlpatterns = [
    path('', views.barcha_hodimlar, name='barcha_hodimlar'),

    # Hodim management (cleaned up duplicates)
    path('hodim_list/', views.hodim_list, name='hodim_list'),
    path('add-hodim/', views.add_hodim, name='add_hodim'),
    path("hodimlar/<int:id>/edit/", views.edit_hodim, name="edit_hodim"),  
    path("hodimlar/<int:id>/delete/", views.delete_hodim, name="delete_hodim"),
    path('hodim/<int:hodim_id>/', views.hodim_detail, name='hodim_detail'),
    
    # Reports and statistics
    path('barcha-hodimlar/', barcha_hodimlar, name='barcha_hodimlar'),
    path('bugungi-holati/', bugungi_keldi_kelmadi, name='bugungi_holati'),
    path("hodimlar/monthly_report/", views.monthly_report, name="monthly_report"),
    path('monthly-work-hours/', views.monthly_work_hours, name='monthly_work_hours'),
   
    # Worklog management
    path('add_worklog/<int:hodim_id>/', add_worklog, name='add_worklog'),
    path('worklogs/', worklog_list, name='worklog_list'),
    path("worklogs/export_excel/", views.export_to_excel, name="export_to_excel"),
    path("worklogs/export_pdf/", views.export_to_pdf, name="export_pdf"),
    path("worklogs/chart/", views.worklog_chart_data, name="worklog_chart_data"),

    # Admin tizimga kirish
    path("admin_login/", views.admin_login, name="admin_login"),
    path("admin_logout/", views.admin_logout, name="admin_logout"),
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),

    # Parolni unutganlar uchun reset sahifalari
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset_done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset_done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    
    # RFID API endpoints
    path('api/rfid/', views.rfid_api, name='rfid_api'),
    path('api/rfid/recent/', views.get_recent_rfid_scans, name='recent_rfid_scans'),
    path('api/rfid/clear/', views.clear_rfid_scans, name='clear_rfid_scans'),
    
    # Google Sheets API endpoints
    path('api/google-sheets/sync/', views.google_sheets_sync, name='google_sheets_sync'),
    path('api/google-sheets/create/', views.google_sheets_create, name='google_sheets_create'),
    path('api/google-sheets/read/<str:spreadsheet_id>/', views.google_sheets_read, name='google_sheets_read'),
    path('api/google-sheets/append/', views.google_sheets_append, name='google_sheets_append'),
    path('google-sheets-settings/', views.google_sheets_settings, name='google_sheets_settings'),
    
    # path("export/excel/", export_to_excel, name="export_excel"),
    
]
