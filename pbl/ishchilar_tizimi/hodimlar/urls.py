from django.urls import path
from . import views
from .views import home_view

urlpatterns = [
    path('', views.hodim_list, name='hodim_list'),
    path('add/', views.add_hodim, name='add_hodim'),
    path('worklog/<int:hodim_id>/', views.add_worklog, name='add_worklog'),
    path('report/', views.monthly_report, name='monthly_report'),
    path('', home_view, name='home'),
]
