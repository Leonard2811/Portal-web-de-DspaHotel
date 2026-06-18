from django.db import models
from django.contrib.auth.models import User
from core.models import Room
from datetime import date


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    address = models.TextField(verbose_name="Dirección")
    id_document = models.CharField(max_length=50, verbose_name="Cédula/Pasaporte")
    birth_date = models.DateField(verbose_name="Fecha de Nacimiento")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.id_document}"


class Reservation(models.Model):
    SERVICE_CHOICES = [
        ('room', 'Habitación'),
        ('gym', 'Gimnasio'),
        ('spa', 'Spa'),
        ('sauna', 'Sauna'),
        ('jacuzzi', 'Jacuzzi'),
        ('pool', 'Piscina'),
        ('event_room', 'Salón de Eventos'),
        ('conference', 'Sala de Conferencias'),
        ('restaurant', 'Restaurante'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pendiente de Pago'),
        ('payment_uploaded', 'Comprobante Subido'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Cliente", related_name='reservations')
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, verbose_name="Servicio")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Habitación")
    check_in = models.DateField(verbose_name="Check-in")
    check_out = models.DateField(verbose_name="Check-out")
    adults_count = models.IntegerField(default=1, verbose_name="Adultos")
    children_count = models.IntegerField(default=0, verbose_name="Niños")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Total")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Estado")
    special_requests = models.TextField(blank=True, verbose_name="Peticiones Especiales")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Reservación"
        verbose_name_plural = "Reservaciones"

    def __str__(self):
        return f"Reservación #{self.id} - {self.customer}"

    def is_active(self):
        return self.check_out >= date.today() and self.status in ['confirmed', 'payment_uploaded']

    def nights(self):
        if self.check_in and self.check_out:
            return (self.check_out - self.check_in).days
        return 0


class PaymentProof(models.Model):
    VERIFICATION_CHOICES = [
        ('pending', 'Pendiente'),
        ('verified', 'Verificado'),
        ('rejected', 'Rechazado'),
    ]

    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='payments', verbose_name="Reservación")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Pago")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    proof_image = models.ImageField(upload_to='payment_proofs/', verbose_name="Comprobante")
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='pending', verbose_name="Estado de Verificación")
    staff_notes = models.TextField(blank=True, verbose_name="Notas del Staff")

    class Meta:
        verbose_name = "Comprobante de Pago"
        verbose_name_plural = "Comprobantes de Pago"

    def __str__(self):
        return f"Pago de {self.reservation}"


class RoomAvailability(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="Habitación")
    date = models.DateField(verbose_name="Fecha")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")

    class Meta:
        unique_together = ['room', 'date']
        verbose_name = "Disponibilidad"
        verbose_name_plural = "Disponibilidades"

    def __str__(self):
        return f"{self.room} - {self.date}"
