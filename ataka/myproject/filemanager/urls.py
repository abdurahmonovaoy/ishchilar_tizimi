from django.urls import path
from .views import index, download_zip

urlpatterns = [
    path("", index, name="index"),
    path("download/", download_zip, name="download_zip"),
]
