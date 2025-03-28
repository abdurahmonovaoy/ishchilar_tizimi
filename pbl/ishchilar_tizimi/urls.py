from django.contrib import admin
from django.urls import path, include
from hodimlar.views import home_view  

urlpatterns = [
    # path('', home_view, name='home'),  # Asosiy sahifa
    # path('hodimlar/', include('hodimlar.urls')),  # Hodimlar ilovasining URL-lari
    path('admin/', admin.site.urls),  # Bu qatorni tekshiring
    path('', include('hodimlar.urls')),
]
# path('admin/', admin.site.urls),  # Django admin paneli   mani rosa asbimi buzgan narsa