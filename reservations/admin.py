from django.contrib import admin
from .models import Customer, Reservation, PaymentProof, RoomAvailability, ServiceReservation, ServicePaymentProof, EventInquiry


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
    list_display = ('id', 'customer', 'service_type', 'room', 'get_room_floor', 'get_room_channel', 'check_in', 'check_out', 'status', 'total_price')
    list_filter = ('status', 'service_type', 'room__floor', 'room__sales_channel', 'check_in')
    search_fields = ('customer__user__first_name', 'customer__user__last_name', 'customer__id_document')
    ordering = ('-created_at',)

    @admin.display(description='Piso', ordering='room__floor')
    def get_room_floor(self, obj):
        return obj.room.floor if obj.room else '-'

    @admin.display(description='Canal', ordering='room__sales_channel')
    def get_room_channel(self, obj):
        return obj.room.get_sales_channel_display() if obj.room else '-'
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


class ServicePaymentProofInline(admin.TabularInline):
    model = ServicePaymentProof
    extra = 0
    readonly_fields = ('payment_date',)


@admin.register(ServiceReservation)
class ServiceReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'service_category', 'service_name', 'price', 'preferred_date', 'status')
    list_filter = ('status', 'service_category', 'preferred_date')
    search_fields = ('customer__user__first_name', 'customer__user__last_name', 'service_name')
    ordering = ('-created_at',)
    inlines = [ServicePaymentProofInline]

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        return False


@admin.register(ServicePaymentProof)
class ServicePaymentProofAdmin(admin.ModelAdmin):
    list_display = ('service_reservation', 'amount', 'verification_status', 'payment_date')
    list_filter = ('verification_status',)


@admin.register(EventInquiry)
class EventInquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'event_type', 'salon_preference', 'estimated_guests', 'preferred_date', 'is_read', 'is_responded')
    list_filter = ('event_type', 'salon_preference', 'is_read', 'is_responded')
    search_fields = ('name', 'email', 'message')
    ordering = ('-created_at',)
