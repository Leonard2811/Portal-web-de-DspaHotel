from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('reservations/', include('reservations.urls')),
    path('staff/', include('staff.urls')),
]

# Servir archivos media siempre (en PythonAnywhere se puede configurar
# el path de media en la pestaña Web > Static files, pero esto funciona
# como fallback)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
