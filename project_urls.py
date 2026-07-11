from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

print("=== LOADING PROJECT URLS ===")

urlpatterns = [
    path('admin/',   admin.site.urls),
    path('',         include('cabs.urls')),
    path('portal/',  include('driver_portal.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
