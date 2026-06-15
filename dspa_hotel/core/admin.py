from django.contrib import admin
from .models import HotelInfo, Service, Room, RoomImage, ContactInfo


@admin.register(HotelInfo)
class HotelInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Información General', {'fields': ('name', 'description', 'logo', 'facade_image')}),
        ('Misión y Visión', {'fields': ('mission', 'vision')}),
        ('Detalles', {'fields': ('objectives', 'value_proposition', 'competitive_advantages', 'values')}),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    ordering = ('order', 'name')


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'status', 'price_per_night', 'is_active')
    list_filter = ('room_type', 'status', 'is_active')
    search_fields = ('room_number',)
    inlines = [RoomImageInline]


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'whatsapp_number')
