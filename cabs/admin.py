from django.contrib import admin
from .models import Booking, Driver, ContactMessage


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['driver_id', 'name', 'phone', 'vehicle_number', 'vehicle_type', 'vehicle_model', 'is_available', 'is_active']
    list_filter  = ['vehicle_type', 'is_available', 'is_active']
    search_fields = ['name', 'driver_id', 'vehicle_number', 'phone']
    list_editable = ['is_available', 'is_active']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ['booking_id', 'customer_name', 'customer_phone', 'pickup_city', 'drop_city', 'pickup_date', 'cab_type', 'status', 'driver', 'estimated_fare']
    list_filter   = ['status', 'cab_type', 'pickup_city', 'drop_city', 'trip_type']
    search_fields = ['booking_id', 'customer_name', 'customer_phone']
    list_editable = ['status', 'driver']
    raw_id_fields = ['driver']


@admin.register(ContactMessage)
class ContactAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'phone', 'created_at']
    readonly_fields = ['created_at']
