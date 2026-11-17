from django.db import models
from django.contrib.auth.models import User


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    position = models.CharField(max_length=100, verbose_name="Cargo")
    department = models.CharField(max_length=100, verbose_name="Departamento")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    can_verify_payments = models.BooleanField(default=False, verbose_name="Puede Verificar Pagos")
    can_manage_reservations = models.BooleanField(default=False, verbose_name="Puede Gestionar Reservas")
    can_view_reports = models.BooleanField(default=False, verbose_name="Puede Ver Reportes")

    class Meta:
        verbose_name = "Perfil de Staff"
        verbose_name_plural = "Perfiles de Staff"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"


class AuditLog(models.Model):
    """Modelo para registrar todas las acciones importantes del sistema"""
    ACTION_CHOICES = [
        ('login', 'Inicio de Sesión'),
        ('logout', 'Cierre de Sesión'),
        ('verify_payment', 'Pago Verificado'),
        ('reject_payment', 'Pago Rechazado'),
        ('update_status', 'Estado de Reservación Actualizado'),
        ('delete_reservation', 'Reservación Eliminada'),
        ('create_user', 'Usuario Creado'),
        ('edit_user', 'Usuario Editado'),
        ('delete_user', 'Usuario Eliminado'),
        ('room_update', 'Habitación Actualizada'),
        ('backup_created', 'Respaldo Creado'),
        ('backup_restored', 'Respaldo Restaurado'),
        ('backup_deleted', 'Respaldo Eliminado'),
        ('service_verify', 'Pago de Servicio Verificado'),
        ('service_reject', 'Pago de Servicio Rechazado'),
        ('service_status', 'Estado de Servicio Actualizado'),
        ('service_delete', 'Reserva de Servicio Eliminada'),
        ('event_created', 'Consulta de Evento Registrada'),
        ('event_deleted', 'Consulta de Evento Eliminada'),
        ('event_read', 'Consulta de Evento Marcada'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuario")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="Acción")
    description = models.TextField(verbose_name="Descripción")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
