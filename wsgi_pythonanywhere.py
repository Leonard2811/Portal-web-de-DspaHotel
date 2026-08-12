"""
WSGI configuration for PythonAnywhere.

Copia este contenido en el archivo WSGI que te da PythonAnywhere
(lo encuentras en la pestana Web > WSGI configuration file).

IMPORTANTE: Reemplaza 'TU_USUARIO' con tu nombre de usuario de PythonAnywhere.
"""

import os
import sys

# Reemplaza 'TU_USUARIO' con tu nombre de usuario de PythonAnywhere
path = '/home/TU_USUARIO/Portal_Web_Dspahotel'

if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'dspa_hotel.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
