from django.db import models


class HotelInfo(models.Model):
    name = models.CharField(max_length=200, default="D'Spa Hotel")
    mission = models.TextField(verbose_name="Misión")
    vision = models.TextField(verbose_name="Visión")
    description = models.TextField(verbose_name="Descripción General")
    objectives = models.TextField(verbose_name="Objetivos", help_text="Separar con punto y coma")
    value_proposition = models.TextField(verbose_name="Propuesta de Valor")
    competitive_advantages = models.TextField(verbose_name="Ventajas Competitivas", help_text="Separar con punto y coma")
    values = models.TextField(verbose_name="Valores", help_text="Separar con punto y coma")
    logo = models.ImageField(upload_to='logo/', verbose_name="Logo", blank=True, null=True)
    facade_image = models.ImageField(upload_to='facade/', verbose_name="Fachada", blank=True, null=True)

    class Meta:
        verbose_name = "Información del Hotel"
        verbose_name_plural = "Información del Hotel"

    def __str__(self):
        return self.name

    def get_objectives_list(self):
        return [obj.strip() for obj in self.objectives.split(';') if obj.strip()]

    def get_values_list(self):
        return [val.strip() for val in self.values.split(';') if val.strip()]

    def get_advantages_list(self):
        return [adv.strip() for adv in self.competitive_advantages.split(';') if adv.strip()]


class Service(models.Model):
    CATEGORY_CHOICES = [
        ('wellness', 'Bienestar'),
        ('corporate', 'Corporativo'),
        ('general', 'General'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripción")
    image = models.ImageField(upload_to='services/', verbose_name="Imagen", blank=True, null=True)
    icon_class = models.CharField(max_length=100, verbose_name="Clase de Icono", help_text="Ej: fas fa-spa")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general', verbose_name="Categoría")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.IntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return self.name


class Room(models.Model):
    ROOM_TYPES = [
        ('matrimonial', 'Habitación Deluxe Matrimonial'),
        ('double', 'Habitación Deluxe Doble'),
    ]
    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('occupied', 'Ocupada'),
        ('maintenance', 'Mantenimiento'),
        ('reserved', 'Reservada'),
    ]

    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, verbose_name="Tipo")
    room_number = models.CharField(max_length=10, unique=True, verbose_name="Número")
    description = models.TextField(verbose_name="Descripción")
    detailed_description = models.TextField(verbose_name="Descripción Detallada", help_text="Incluir amenities y características")
    capacity_adults = models.IntegerField(default=2, verbose_name="Capacidad Adultos")
    capacity_children = models.IntegerField(default=1, verbose_name="Capacidad Niños")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio por Noche")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name="Estado")
    has_terrace = models.BooleanField(default=True, verbose_name="Terraza")
    has_safe = models.BooleanField(default=True, verbose_name="Caja Fuerte")
    has_tv = models.BooleanField(default=True, verbose_name="TV")
    has_closet = models.BooleanField(default=True, verbose_name="Closet")
    has_minibar = models.BooleanField(default=False, verbose_name="Mini Nevera")
    has_balcony = models.BooleanField(default=False, verbose_name="Balcón")
    is_active = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        ordering = ['room_type', 'room_number']
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"

    def __str__(self):
        return f"{self.get_room_type_display()} - {self.room_number}"

    def is_available(self):
        return self.status == 'available'


class RoomImage(models.Model):
    room = models.ForeignKey(Room, related_name='images', on_delete=models.CASCADE, verbose_name="Habitación")
    image = models.ImageField(upload_to='rooms/', verbose_name="Imagen")
    title = models.CharField(max_length=200, verbose_name="Título")
    order = models.IntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering = ['order']
        verbose_name = "Imagen de Habitación"
        verbose_name_plural = "Imágenes de Habitaciones"

    def __str__(self):
        return f"Imagen {self.order} de {self.room}"


class ContactInfo(models.Model):
    whatsapp_number = models.CharField(max_length=20, default="584248304994", verbose_name="WhatsApp")
    whatsapp_link = models.URLField(default="https://api.whatsapp.com/send?phone=584248304994", verbose_name="Link WhatsApp")
    instagram_username = models.CharField(max_length=100, default="dspahotel", verbose_name="Instagram")
    instagram_link = models.URLField(default="https://www.instagram.com/dspahotel?igsh=ZjAwOHc0YXowZHBy", verbose_name="Link Instagram")
    email = models.EmailField(default="Dspahotelreservaciones@gmail.com", verbose_name="Correo")
    phone = models.CharField(max_length=20, default="+58 424-8304994", verbose_name="Teléfono")
    address = models.TextField(default="AV. Intercomunal, Lecheria, VE 6016", verbose_name="Dirección")
    google_maps_embed = models.TextField(
        verbose_name="Google Maps Embed",
        help_text="Pegar código iframe completo",
        default='<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3921.5!2d-64.7!3d10.2!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTDCsDEyJzAwLjAiTiA2NMKwNDInMDAuMCJX!5e0!3m2!1ses!2sve!4v1234567890" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>'
    )

    class Meta:
        verbose_name = "Información de Contacto"
        verbose_name_plural = "Información de Contacto"

    def __str__(self):
        return "Información de Contacto del Hotel"
