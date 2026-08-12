from django.contrib import admin
from .models import HotelInfo, Service, Room, RoomImage, ContactInfo


@admin.register(HotelInfo)
class HotelInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Información General', {'fields': ('name', 'description', 'logo', 'facade_image')}),
        ('Misión y Visión', {'fields': ('mission', 'vision')}),
        ('Detalles', {'fields': ('objectives', 'value_proposition', 'competitive_advantages', 'values')}),
    )

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


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    ordering = ('order', 'name')

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


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'status', 'price_per_night', 'is_active')
    list_filter = ('room_type', 'status', 'is_active')
    search_fields = ('room_number',)
    inlines = [RoomImageInline]

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


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'whatsapp_number')

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
