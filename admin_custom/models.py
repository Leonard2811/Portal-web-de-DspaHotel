from django.db import models
from django.contrib.auth.models import User


class PlanillaComprador(models.Model):
    """
    Modelo para registrar la información de compradores/clientes del hotel.
    Incluye permisos personalizados que se asignan a los diferentes roles
    de administrador del sistema.
    """

    TIPO_DOCUMENTO_CHOICES = [
        ('V', 'Venezolano(a)'),
        ('E', 'Extranjero(a)'),
        ('P', 'Pasaporte'),
        ('J', 'Jurídico'),
    ]

    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('zelle', 'Zelle'),
        ('paypal', 'PayPal'),
        ('otro', 'Otro'),
    ]

    # Información personal
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    tipo_documento = models.CharField(
        max_length=1, choices=TIPO_DOCUMENTO_CHOICES,
        default='V', verbose_name="Tipo de Documento"
    )
    numero_documento = models.CharField(
        max_length=20, unique=True, verbose_name="Número de Documento"
    )
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Correo Electrónico", blank=True)
    direccion = models.TextField(verbose_name="Dirección", blank=True)

    # Información de compra/reserva
    servicio_adquirido = models.CharField(
        max_length=200, verbose_name="Servicio Adquirido"
    )
    monto_total = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Monto Total"
    )
    metodo_pago = models.CharField(
        max_length=20, choices=METODO_PAGO_CHOICES,
        default='efectivo', verbose_name="Método de Pago"
    )
    referencia_pago = models.CharField(
        max_length=100, verbose_name="Referencia de Pago", blank=True
    )
    comprobante = models.ImageField(
        upload_to='comprobantes/', verbose_name="Comprobante de Pago",
        blank=True, null=True
    )

    # Metadatos
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='planillas_creadas', verbose_name="Creado por"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True, verbose_name="Última Actualización"
    )
    observaciones = models.TextField(
        verbose_name="Observaciones", blank=True
    )

    class Meta:
        verbose_name = "Planilla de Comprador"
        verbose_name_plural = "Planillas de Compradores"
        ordering = ['-fecha_creacion']
        permissions = [
            ("puede_ver_planilla", "Puede ver planillas de compradores"),
            ("puede_crear_planilla", "Puede crear planillas de compradores"),
            ("puede_editar_planilla", "Puede editar planillas de compradores"),
            ("puede_eliminar_planilla", "Puede eliminar planillas de compradores"),
            ("puede_exportar_planilla", "Puede exportar planillas de compradores"),
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.get_tipo_documento_display()}-{self.numero_documento}"

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    nombre_completo.short_description = "Nombre Completo"
