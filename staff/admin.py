from django.contrib import admin
from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'department', 'can_verify_payments', 'can_manage_reservations')
    list_filter = ('department', 'can_verify_payments', 'can_manage_reservations')
    search_fields = ('user__first_name', 'user__last_name', 'position')

    def has_change_permission(self, request, obj=None):
        """Solo Super Administradores pueden modificar perfiles de staff."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        if request.user.groups.filter(name='Recepcionistas de Datos').exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Solo Super Administradores pueden eliminar perfiles de staff."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        return False

    def has_add_permission(self, request):
        """Solo Super Administradores pueden crear perfiles de staff."""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Super Administradores').exists():
            return True
        if request.user.groups.filter(name='Recepcionistas de Datos').exists():
            return False
        return super().has_add_permission(request)
