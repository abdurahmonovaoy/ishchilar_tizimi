from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os
import zipfile
from django.conf import settings

# Fayllarni saqlash joyi
UPLOAD_FOLDER = os.path.join(settings.MEDIA_ROOT, 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def index(request):
    """ Bosh sahifa: Fayllarni yuklash va ko'rish """
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        fs = FileSystemStorage(location=UPLOAD_FOLDER)
        fs.save(file.name, file)

    files = os.listdir(UPLOAD_FOLDER)
    return render(request, "filemanager/index.html", {"files": files})

def download_zip(request):
    """ Tanlangan fayllarni ZIP qilish va yuklash """
    selected_files = request.GET.getlist("files")
    zip_path = os.path.join(settings.MEDIA_ROOT, "download.zip")

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in selected_files:
            file_path = os.path.join(UPLOAD_FOLDER, file)
            zipf.write(file_path, file)

    with open(zip_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="files.zip"'
        return response
