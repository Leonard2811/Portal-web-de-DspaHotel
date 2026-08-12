"""
Management command: init_admins
Crea un unico superusuario y los 3 grupos de administracion
con permisos especificos.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission


class Command(BaseCommand):
    help = (
        'Crea los 3 grupos de administracion y un unico '
        'superusuario admin para gestionar todo el sistema.'
    )

    def handle(self, *args, **options):
        self.stdout.write(
            '\n==================================================='
        )
        self.stdout.write(
            '  INICIALIZACION DE ROLES Y USUARIOS - D\'Spa Hotel'
        )
        self.stdout.write(
            '===================================================\n'
        )

        # --------------------------------------------------
        # GRUPO 1: Super Administradores -- TODO el poder
        # --------------------------------------------------
        group_super, created = Group.objects.get_or_create(
            name='Super Administradores'
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                '  [OK] Grupo "Super Administradores" creado'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '  [!] Grupo "Super Administradores" ya existia'
            ))

        all_permissions = Permission.objects.all()
        group_super.permissions.set(all_permissions)
        self.stdout.write(f'    -> {all_permissions.count()} permisos asignados')

        # --------------------------------------------------
        # GRUPO 2: Encargados de Reservaciones
        # --------------------------------------------------
        group_encargados, created = Group.objects.get_or_create(
            name='Encargados de Reservaciones'
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                '  [OK] Grupo "Encargados de Reservaciones" creado'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '  [!] Grupo "Encargados de Reservaciones" ya existia'
            ))

        view_permissions = Permission.objects.filter(
            codename__startswith='view_'
        )
        add_permissions = Permission.objects.filter(
            codename__startswith='add_'
        ).exclude(
            content_type__model__in=['user', 'group', 'permission', 'logentry']
        )
        change_permissions = Permission.objects.filter(
            codename__startswith='change_'
        ).exclude(
            content_type__model__in=['user', 'group', 'permission', 'logentry']
        )
        custom_permissions = Permission.objects.filter(
            codename__in=[
                'puede_ver_planilla',
                'puede_crear_planilla',
                'puede_editar_planilla',
            ]
        )

        encargados_perms = (
            view_permissions | add_permissions |
            change_permissions | custom_permissions
        )
        group_encargados.permissions.set(encargados_perms)
        self.stdout.write(
            f'    -> {encargados_perms.count()} permisos asignados'
        )

        # --------------------------------------------------
        # GRUPO 3: Recepcionistas de Datos -- Solo lectura
        # --------------------------------------------------
        group_recepcion, created = Group.objects.get_or_create(
            name='Recepcionistas de Datos'
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                '  [OK] Grupo "Recepcionistas de Datos" creado'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '  [!] Grupo "Recepcionistas de Datos" ya existia'
            ))

        recepcion_perms = view_permissions | Permission.objects.filter(
            codename='puede_ver_planilla'
        )
        group_recepcion.permissions.set(recepcion_perms)
        self.stdout.write(
            f'    -> {recepcion_perms.count()} permisos asignados (solo lectura)'
        )

        # --------------------------------------------------
        # CREAR UNICO SUPERUSUARIO
        # --------------------------------------------------
        self.stdout.write(
            '\n--- Creando superusuario ---\n'
        )

        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Administrador',
                'last_name': 'Principal',
                'email': 'admin@dspahotel.com',
                'is_superuser': True,
                'is_staff': True,
            }
        )

        if created:
            user.set_password('admin2024')
            user.save()
            user.groups.add(group_super)
            self.stdout.write(self.style.SUCCESS(
                '  [OK] Superusuario "admin" creado'
            ))
        else:
            user.groups.add(group_super)
            self.stdout.write(self.style.WARNING(
                '  [!] Superusuario "admin" ya existia'
            ))

        # --------------------------------------------------
        # RESUMEN FINAL
        # --------------------------------------------------
        self.stdout.write(
            '\n==================================================='
        )
        self.stdout.write(self.style.SUCCESS(
            '  [OK] INICIALIZACION COMPLETADA EXITOSAMENTE'
        ))
        self.stdout.write(
            '===================================================\n'
        )
        self.stdout.write(
            '  Credenciales de acceso:\n'
            '  +-------------------+----------------+\n'
            '  | Usuario           | Contrasena     |\n'
            '  +-------------------+----------------+\n'
            '  | admin             | admin2024      |\n'
            '  +-------------------+----------------+\n'
            '\n'
            '  Desde el panel, puedes crear mas usuarios\n'
            '  de staff con diferentes roles y permisos.\n'
            '  URL: /staff/users/\n'
        )
