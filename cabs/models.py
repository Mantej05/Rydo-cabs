from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random, string

CITY_CHOICES = [
    ('Chandigarh', 'Chandigarh'), ('Delhi', 'Delhi'), ('Amritsar', 'Amritsar'),
    ('Shimla', 'Shimla'), ('Jammu', 'Jammu'), ('Srinagar', 'Srinagar'),
    ('Jaipur', 'Jaipur'), ('Manali', 'Manali'),
]
CAB_TYPE_CHOICES = [
    ('sedan', 'Sedan (4 Seater)'), ('suv', 'SUV (6 Seater)'), ('tempo', 'Tempo Traveller (12 Seater)'),
]
BOOKING_STATUS = [
    ('pending', 'Pending'), ('confirmed', 'Confirmed'), ('on_trip', 'On Trip'),
    ('completed', 'Completed'), ('cancelled', 'Cancelled'),
]


class Driver(models.Model):
    user         = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver')
    driver_id    = models.CharField(max_length=10, unique=True, blank=True)
    name         = models.CharField(max_length=100)
    phone        = models.CharField(max_length=15)
    license_number = models.CharField(max_length=50, unique=True)
    vehicle_number = models.CharField(max_length=20, unique=True)
    vehicle_type   = models.CharField(max_length=20, choices=CAB_TYPE_CHOICES)
    vehicle_model  = models.CharField(max_length=100)
    is_available   = models.BooleanField(default=True)
    is_active      = models.BooleanField(default=True)
    current_lat    = models.FloatField(null=True, blank=True)
    current_lng    = models.FloatField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    joined_date    = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.driver_id:
            self.driver_id = 'DRV-' + ''.join(random.choices(string.digits, k=4))
        super().save(*args, **kwargs)

    def total_rides(self):
        return self.booking_set.filter(status='completed').count()

    def total_earnings(self):
        from django.db.models import Sum
        r = self.booking_set.filter(status='completed').aggregate(Sum('estimated_fare'))
        return r['estimated_fare__sum'] or 0

    def __str__(self):
        return f"{self.driver_id} | {self.name} - {self.vehicle_number}"


class Booking(models.Model):
    booking_id     = models.CharField(max_length=20, unique=True, blank=True)
    # Customer
    customer_name  = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    customer_email = models.EmailField(blank=True)
    # Trip
    pickup_city    = models.CharField(max_length=50, choices=CITY_CHOICES)
    drop_city      = models.CharField(max_length=50, choices=CITY_CHOICES)
    pickup_date    = models.DateField()
    pickup_time    = models.TimeField()
    cab_type       = models.CharField(max_length=20, choices=CAB_TYPE_CHOICES)
    passengers     = models.PositiveIntegerField(default=1)
    trip_type      = models.CharField(max_length=20, choices=[('one_way','One Way'),('round_trip','Round Trip')], default='one_way')
    return_date    = models.DateField(null=True, blank=True)
    # Fare & status
    estimated_fare   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission_rate  = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    status           = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    driver           = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL)
    accepted_at      = models.DateTimeField(null=True, blank=True)
    completed_at     = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(default=timezone.now)

    def driver_earning(self):
        if self.estimated_fare:
            return round(float(self.estimated_fare) * (1 - float(self.commission_rate) / 100), 2)
        return 0

    def admin_commission(self):
        if self.estimated_fare:
            return round(float(self.estimated_fare) * float(self.commission_rate) / 100, 2)
        return 0

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = 'Rydo-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_id} | {self.customer_name} | {self.pickup_city} to {self.drop_city}"


class ContactMessage(models.Model):
    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    phone      = models.CharField(max_length=15, blank=True)
    message    = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d %b %Y')}"
