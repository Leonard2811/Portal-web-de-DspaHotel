#!/usr/bin/env python
"""
Script de inicializacion para PythonAnywhere.
Ejecutar una sola vez despues de clonar el repositorio en PythonAnywhere.

Uso en la consola Bash de PythonAnywhere:
    cd ~/Portal_Web_Dspahotel
    python setup_pythonanywhere.py
"""
import subprocess
import sys
import os


def run(cmd, description=""):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n{'='*50}")
    print(f"  {description}")
    print(f"  $ {cmd}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"  [ERROR] {result.stderr}")
    return result.returncode == 0


def main():
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║     SETUP D'SPA HOTEL - PythonAnywhere            ║
    ╚═══════════════════════════════════════════════════╝
    """)

    python = sys.executable

    # 1. Instalar dependencias
    run(f"{python} -m pip install -r requirements.txt",
        "Instalando dependencias...")

    # 2. Ejecutar migraciones
    run(f"{python} manage.py migrate",
        "Ejecutando migraciones de base de datos...")

    # 3. Cargar datos iniciales (habitaciones, servicios, info del hotel)
    run(f"{python} manage.py loaddata core/fixtures/initial_data.json",
        "Cargando datos iniciales (habitaciones, servicios, etc.)...")

    # 4. Crear usuarios administradores
    run(f"{python} manage.py init_admins",
        "Creando usuarios administradores...")

    # 5. Recopilar archivos estaticos
    run(f"{python} manage.py collectstatic --noinput",
        "Recopilando archivos estaticos...")

    print("""
    ╔═══════════════════════════════════════════════════╗
    ║                  SETUP COMPLETO                   ║
    ╠═══════════════════════════════════════════════════╣
    ║                                                   ║
    ║  Ahora configura tu Web App en PythonAnywhere:    ║
    ║                                                   ║
    ║  1. Ve a la pestana "Web"                         ║
    ║  2. Crea una nueva Web App                        ║
    ║  3. Selecciona "Manual configuration"             ║
    ║  4. Selecciona Python 3.10                        ║
    ║  5. En "Source code", pon:                        ║
    ║     /home/TU_USUARIO/Portal_Web_Dspahotel        ║
    ║  6. En "WSGI configuration file", edita y pon    ║
    ║     el contenido del archivo wsgi_pythonanywhere  ║
    ║  7. En "Static files":                            ║
    ║     URL: /static/                                 ║
    ║     Dir: /home/TU_USUARIO/Portal_Web_Dspahotel   ║
    ║          /staticfiles                             ║
    ║     URL: /media/                                  ║
    ║     Dir: /home/TU_USUARIO/Portal_Web_Dspahotel   ║
    ║          /media                                   ║
    ║  8. Haz clic en "Reload"                          ║
    ║                                                   ║
    ║  Credenciales admin:                              ║
    ║  admin_supremo / admin123                         ║
    ║  reservas_admin / reservas123                     ║
    ║  recepcion_admin / recepcion123                   ║
    ║                                                   ║
    ╚═══════════════════════════════════════════════════╝
    """)


if __name__ == '__main__':
    main()
