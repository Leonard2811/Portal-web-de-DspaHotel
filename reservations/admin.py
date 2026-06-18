from django.contrib import admin
from .models import Customer, Reservation, PaymentProof, RoomAvailability


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'id_document', 'phone')
    search_fields = ('user__first_name', 'user__last_name', 'id_document')


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


@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'amount', 'verification_status', 'payment_date')
    list_filter = ('verification_status',)


@admin.register(RoomAvailability)
class RoomAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('room', 'date', 'is_available')
    list_filter = ('is_available', 'date')
