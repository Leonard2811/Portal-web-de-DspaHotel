from django.contrib import admin
from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'department', 'can_verify_payments', 'can_manage_reservations')
    list_filter = ('department', 'can_verify_payments', 'can_manage_reservations')
    search_fields = ('user__first_name', 'user__last_name', 'position')
