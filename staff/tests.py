import os
import shutil
from pathlib import Path
from datetime import datetime, date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.conf import settings
from staff.models import StaffProfile, AuditLog
from staff.views import log_audit, _get_user_role


class StaffFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear grupos de roles
        self.group_super = Group.objects.create(name='Super Administradores')
        self.group_encargado = Group.objects.create(name='Encargados de Reservaciones')
        self.group_recepcionista = Group.objects.create(name='Recepcionistas de Datos')
        self.group_operador = Group.objects.create(name='Operadores Aqua Spa Gym')

        # 1. Superusuario
        self.superuser = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123',
            first_name='Admin',
            last_name='Principal'
        )
        self.superuser.groups.add(self.group_super)

        # 2. Encargado de reservaciones
        self.encargado = User.objects.create_user(
            username='encargado_test',
            email='encargado@test.com',
            password='password123',
            first_name='Carlos',
            last_name='Encargado',
            is_staff=True
        )
        self.encargado.groups.add(self.group_encargado)

        # 3. Recepcionista (solo lectura)
        self.recepcionista = User.objects.create_user(
            username='recep_test',
            email='recep@test.com',
            password='password123',
            first_name='Ana',
            last_name='Recepcionista',
            is_staff=True
        )
        self.recepcionista.groups.add(self.group_recepcionista)

        # 4. Operador Aqua Spa Gym
        self.operador = User.objects.create_user(
            username='aqua_test',
            email='aqua@test.com',
            password='password123',
            first_name='Marcos',
            last_name='Operador',
            is_staff=True
        )
        self.operador.groups.add(self.group_operador)

        # 5. Cliente regular (sin permisos de staff)
        self.cliente = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='password123',
            first_name='Pedro',
            last_name='Cliente',
            is_staff=False
        )

        # Directorio temporal de respaldos para pruebas
        self.backup_dir = Path(settings.BASE_DIR) / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        self._start_time = datetime.now().timestamp()

    def tearDown(self):
        # Limpiar cualquier archivo creado en backups/ durante las pruebas
        if self.backup_dir.exists():
            for f in list(self.backup_dir.glob('db_backup_*.sqlite3')) + list(self.backup_dir.glob('db_pre_restore_*.sqlite3')):
                if 'test' in f.name or (f.stat().st_mtime > getattr(self, '_start_time', 0)):
                    try:
                        f.unlink()
                    except OSError:
                        pass

    # ========================================================
    # 1. PRUEBAS DE SEGURIDAD Y PERMISOS DE ACCESO
    # ========================================================
    def test_anonymous_user_redirected_to_login(self):
        """Usuarios no autenticados deben ser redirigidos al login"""
        urls = [
            reverse('audit_log'),
            reverse('backup_restore'),
            reverse('user_manual'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('login'), response.url)

    def test_regular_customer_denied_access(self):
        """Clientes regulares no deben acceder a ninguna vista de staff"""
        self.client.login(username='cliente_test', password='password123')
        urls = [
            reverse('audit_log'),
            reverse('backup_restore'),
            reverse('user_manual'),
        ]
        for url in urls:
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
            # Redirigido a dashboard o home con mensaje de error
            messages = [m.message for m in response.context['messages']]
            self.assertTrue(any('permisos' in m.lower() for m in messages))

    def test_staff_non_superusers_cannot_access_audit_or_backup(self):
        """Recepcionistas, encargados y operadores NO pueden acceder a auditoría ni respaldos"""
        non_super_staff = [self.encargado, self.recepcionista, self.operador]
        for user in non_super_staff:
            self.client.login(username=user.username, password='password123')
            # Auditoría
            resp_audit = self.client.get(reverse('audit_log'), follow=True)
            messages = [m.message for m in resp_audit.context['messages']]
            self.assertTrue(any('administrador principal' in m.lower() for m in messages))

            # Respaldo
            resp_backup = self.client.get(reverse('backup_restore'), follow=True)
            messages = [m.message for m in resp_backup.context['messages']]
            self.assertTrue(any('administrador principal' in m.lower() for m in messages))

    # ========================================================
    # 2. PRUEBAS DEL HISTORIAL DE AUDITORÍA
    # ========================================================
    def test_audit_log_creation_and_view(self):
        """El superadministrador puede ver el historial y registrar logs"""
        self.client.login(username='admin_test', password='password123')

        # Crear registros de prueba
        AuditLog.objects.create(
            user=self.superuser,
            action='verify_payment',
            description='Pago #99 verificado para reservación #10',
            ip_address='127.0.0.1'
        )
        AuditLog.objects.create(
            user=self.encargado,
            action='update_status',
            description='Reservación #10 actualizada a confirmada',
            ip_address='127.0.0.1'
        )

        response = self.client.get(reverse('audit_log'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Historial de Auditoría')
        self.assertContains(response, 'Pago #99 verificado')
        self.assertContains(response, 'Reservación #10 actualizada')

    def test_audit_log_filters(self):
        """Filtros por tipo de acción y usuario en el historial"""
        self.client.login(username='admin_test', password='password123')

        AuditLog.objects.create(
            user=self.superuser,
            action='backup_created',
            description='Respaldo creado: db_test.sqlite3',
            ip_address='127.0.0.1'
        )
        AuditLog.objects.create(
            user=self.encargado,
            action='room_update',
            description='Habitación 101 actualizada',
            ip_address='127.0.0.1'
        )

        # Filtrar solo por backup_created
        response_action = self.client.get(reverse('audit_log'), {'action': 'backup_created'})
        self.assertEqual(response_action.status_code, 200)
        self.assertContains(response_action, 'Respaldo creado')
        self.assertNotContains(response_action, 'Habitación 101 actualizada')

        # Filtrar por usuario encargado
        response_user = self.client.get(reverse('audit_log'), {'user': str(self.encargado.id)})
        self.assertEqual(response_user.status_code, 200)
        self.assertContains(response_user, 'Habitación 101 actualizada')
        self.assertNotContains(response_user, 'Respaldo creado')

    # ========================================================
    # 3. PRUEBAS DE RESPALDO Y RESTAURACIÓN DE BASE DE DATOS
    # ========================================================
    def test_backup_creation_and_listing(self):
        """El superadministrador puede crear un respaldo de la base de datos"""
        self.client.login(username='admin_test', password='password123')

        response = self.client.post(reverse('backup_restore'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Respaldo creado exitosamente')

        # Verificar que se registró en auditoría
        last_log = AuditLog.objects.first()
        self.assertEqual(last_log.action, 'backup_created')
        self.assertEqual(last_log.user, self.superuser)

        # Verificar que aparece en la tabla
        response_list = self.client.get(reverse('backup_restore'))
        self.assertEqual(response_list.status_code, 200)
        self.assertContains(response_list, 'db_backup_')

    def test_backup_download(self):
        """El superadministrador puede descargar un respaldo existente"""
        self.client.login(username='admin_test', password='password123')

        # Crear un archivo ficticio seguro en la carpeta backups
        test_filename = 'db_backup_test_download.sqlite3'
        test_file_path = self.backup_dir / test_filename
        with open(test_file_path, 'w') as f:
            f.write('fake sqlite content for test')

        url = reverse('download_backup', args=[test_filename])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        response.close()

        # Limpiar
        if test_file_path.exists():
            test_file_path.unlink()

    def test_backup_delete(self):
        """El superadministrador puede eliminar un respaldo existente"""
        self.client.login(username='admin_test', password='password123')

        test_filename = 'db_backup_test_delete.sqlite3'
        test_file_path = self.backup_dir / test_filename
        with open(test_file_path, 'w') as f:
            f.write('dummy')

        url = reverse('delete_backup', args=[test_filename])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'eliminado exitosamente')
        self.assertFalse(test_file_path.exists())

        # Verificar que se registró en auditoría
        last_log = AuditLog.objects.first()
        self.assertEqual(last_log.action, 'backup_deleted')

    # ========================================================
    # 4. PRUEBAS DEL MANUAL DE USO SEGÚN ROL
    # ========================================================
    def test_user_manual_content_for_super_admin(self):
        """Super Admin ve secciones de Usuarios, Auditoría y Respaldos en el manual"""
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('user_manual'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tu rol: Super Administrador')
        self.assertContains(response, 'Gestión de Usuarios')
        self.assertContains(response, 'Historial de Auditoría')
        self.assertContains(response, 'Respaldo y Restauración de Base de Datos')

    def test_user_manual_content_for_encargado(self):
        """Encargado ve reservaciones y pagos, pero NO gestión de usuarios ni auditoría"""
        self.client.login(username='encargado_test', password='password123')
        response = self.client.get(reverse('user_manual'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tu rol: Encargado de Reservaciones')
        self.assertContains(response, 'Gestión de Reservaciones')
        self.assertContains(response, 'Verificación de Comprobantes de Pago')
        self.assertNotContains(response, 'Gestión de Usuarios')
        self.assertNotContains(response, 'Historial de Auditoría')
        self.assertNotContains(response, 'Respaldo y Restauración de Base de Datos')

    def test_user_manual_content_for_recepcionista(self):
        """Recepcionista ve la advertencia de solo lectura y NO ve gestión de usuarios"""
        self.client.login(username='recep_test', password='password123')
        response = self.client.get(reverse('user_manual'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tu rol: Recepcionista de Datos')
        self.assertContains(response, 'Solo puede visualizar las reservaciones')
        self.assertNotContains(response, 'Gestión de Usuarios')
        self.assertNotContains(response, 'Historial de Auditoría')

    def test_user_manual_content_for_operador_aqua(self):
        """Operador Aqua ve módulo Spa & Gym y NO ve Habitaciones ni Usuarios"""
        self.client.login(username='aqua_test', password='password123')
        response = self.client.get(reverse('user_manual'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tu rol: Operador Aqua Spa Gym')
        self.assertContains(response, 'Panel de Control - Spa & Gym')
        self.assertContains(response, 'Reservaciones de Spa & Gym')
        self.assertNotContains(response, 'Gestión de Habitaciones')
        self.assertNotContains(response, 'Gestión de Usuarios')
