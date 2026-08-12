from django.contrib import admin
from .models import Customer, Reservation, PaymentProof, RoomAvailability


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'id_document', 'phone')
    search_fields = ('user__first_name', 'user__last_name', 'id_document')

    def has_change_permission(self, request, obj=None):
        """Solo Super Administradores pueden modificar clientes."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo Super Administradores pueden eliminar clientes."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        return False

    def has_add_permission(self, request):
        """Solo Super Administradores pueden crear clientes."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        return False


class PaymentProofInline(admin.TabularInline):
    model = PaymentProof
    extra = 0
    readonly_fields = ('payment_date',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'service_type', 'room', 'check_in', 'check_out', 'status', 'total_price')
    list_filter = ('status', 'service_type', 'check_in')
    search_fields = ('customer__user__first_name', 'customer__user__last_name', 'customer__id_document')
    ordering = ('-created_at',)
    inlines = [PaymentProofInline]

    def has_change_permission(self, request, obj=None):
        """Encargados pueden editar solo reservaciones que gestionaron."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        if request.user.groups.filter(name='Encargados de Reservaciones').exists():
            return True
        if request.user.groups.filter(name='Recepcionistas de Datos').exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Solo Super Administradores pueden eliminar reservaciones."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        return False

    def has_add_permission(self, request):
        """Recepcionistas NO pueden crear reservaciones."""
        if request.user.groups.filter(name='Recepcionistas de Datos').exists():
            return False
        return super().has_add_permission(request)


@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'amount', 'verification_status', 'payment_date')
    list_filter = ('verification_status',)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Recepcionistas de Datos').exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        return False

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Recepcionistas de Datos').exists():
            return False
        return super().has_add_permission(request)


@admin.register(RoomAvailability)
class RoomAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('room', 'date', 'is_available')
    list_filter = ('is_available', 'date')

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Recepcionistas de Datos').exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        return False
