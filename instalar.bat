@echo off
echo ==================================================
echo   Instalador de Entorno - Portal Web DspaHotel
echo ==================================================
echo.

:: Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH del sistema.
    echo Por favor, instala Python ^(https://www.python.org/downloads/^) y vuelve a ejecutar este script.
    pause
    exit /b
)

echo [OK] Python detectado.
echo.

:: Verificar si existe el entorno virtual, si no, crearlo
if not exist "venv\Scripts\activate.bat" (
    echo Creando entorno virtual (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b
    )
    echo [OK] Entorno virtual creado.
) else (
    echo [OK] Entorno virtual ya existe.
)
echo.

:: Activar entorno e instalar dependencias
echo Activando entorno virtual e instalando dependencias...
call venv\Scripts\activate.bat

echo Actualizando pip...
python -m pip install --upgrade pip >nul 2>&1

if exist requirements.txt (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Ocurrio un problema al instalar los requerimientos.
        pause
        exit /b
    )
    echo [OK] Dependencias instaladas correctamente.
) else (
    echo [ADVERTENCIA] No se encontro el archivo requirements.txt.
)
echo.

:: Aplicar migraciones de la base de datos
if exist manage.py (
    echo Aplicando migraciones de la base de datos...
    python manage.py migrate
    echo [OK] Migraciones aplicadas.
) else (
    echo [ADVERTENCIA] No se encontro manage.py.
)
echo.

echo ==================================================
echo   Instalacion completada con exito.
echo ==================================================
echo.
echo Para iniciar el servidor de desarrollo, ejecuta:
echo venv\Scripts\activate
echo python manage.py runserver
echo.
pause
