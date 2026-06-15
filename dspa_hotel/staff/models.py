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
