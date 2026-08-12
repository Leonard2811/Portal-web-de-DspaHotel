from django.contrib import admin
from .models import PlanillaComprador


@admin.register(PlanillaComprador)
class PlanillaCompradorAdmin(admin.ModelAdmin):
    """
    Configuración del admin para PlanillaComprador.
    Restringe edición y eliminación según el grupo del usuario.
    """

    list_display = (
        'nombre_completo', 'tipo_documento', 'numero_documento',
        'telefono', 'servicio_adquirido', 'monto_total',
        'metodo_pago', 'creado_por', 'fecha_creacion',
    )
    list_filter = ('tipo_documento', 'metodo_pago', 'fecha_creacion')
    search_fields = (
        'nombre', 'apellido', 'numero_documento',
        'email', 'servicio_adquirido',
    )
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    date_hierarchy = 'fecha_creacion'
    list_per_page = 25

    fieldsets = (
        ('Información Personal', {
            'fields': (
                'nombre', 'apellido', 'tipo_documento',
                'numero_documento', 'telefono', 'email', 'direccion',
            ),
        }),
        ('Información de Compra', {
            'fields': (
                'servicio_adquirido', 'monto_total',
                'metodo_pago', 'referencia_pago', 'comprobante',
            ),
        }),
        ('Metadatos', {
            'classes': ('collapse',),
            'fields': (
                'creado_por', 'observaciones',
                'fecha_creacion', 'fecha_actualizacion',
            ),
        }),
    )

    def save_model(self, request, obj, form, change):
        """Asigna automáticamente el usuario que crea la planilla."""
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """
        - Super Administradores: ven TODO.
        - Encargados de Reservaciones: ven solo las planillas que crearon.
        - Recepcionistas de Datos: ven todo (solo lectura).
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name='Encargados de Reservaciones').exists():
            return qs.filter(creado_por=request.user)
        # Recepcionistas y otros ven todo (permisos de vista los controla Django)
        return qs

    def has_change_permission(self, request, obj=None):
        """Encargados solo pueden editar planillas que ellos crearon."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Encargados de Reservaciones').exists():
            if obj is not None:
                return obj.creado_por == request.user
            return True
        if request.user.groups.filter(name='Recepcionistas de Datos').exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Solo Super Administradores pueden eliminar."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        return False

    def has_add_permission(self, request):
        """Recepcionistas NO pueden crear planillas."""
        if request.user.groups.filter(name='Recepcionistas de Datos').exists():
            return False
        return super().has_add_permission(request)
