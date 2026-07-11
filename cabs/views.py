from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from .models import Booking, Driver, ContactMessage
from .forms import BookingForm, TrackBookingForm, ContactForm

FARE_MATRIX = {
    ('Chandigarh','Delhi'):    {'sedan':2800,'suv':3800,'tempo':5500},
    ('Chandigarh','Amritsar'): {'sedan':2000,'suv':2800,'tempo':4000},
    ('Chandigarh','Shimla'):   {'sedan':1800,'suv':2500,'tempo':3800},
    ('Chandigarh','Jammu'):    {'sedan':3000,'suv':4200,'tempo':6000},
    ('Chandigarh','Srinagar'): {'sedan':5500,'suv':7500,'tempo':11000},
    ('Chandigarh','Jaipur'):   {'sedan':5000,'suv':6800,'tempo':9500},
    ('Chandigarh','Manali'):   {'sedan':3500,'suv':4800,'tempo':7000},
}

def get_fare(pickup, drop, cab_type):
    matrix = FARE_MATRIX.get((pickup, drop)) or FARE_MATRIX.get((drop, pickup))
    return matrix.get(cab_type, 0) if matrix else 0


def home(request):
    routes = [
        {'from':'Chandigarh','to':'Delhi',   'distance':'260 km','time':'4-5 hrs'},
        {'from':'Chandigarh','to':'Shimla',  'distance':'115 km','time':'2-3 hrs'},
        {'from':'Chandigarh','to':'Amritsar','distance':'230 km','time':'3-4 hrs'},
        {'from':'Chandigarh','to':'Manali',  'distance':'310 km','time':'7-8 hrs'},
        {'from':'Chandigarh','to':'Jammu',   'distance':'195 km','time':'4-5 hrs'},
        {'from':'Chandigarh','to':'Srinagar','distance':'635 km','time':'11-12 hrs'},
        {'from':'Chandigarh','to':'Jaipur',  'distance':'520 km','time':'8-9 hrs'},
    ]
    return render(request, 'cabs/home.html', {'form': BookingForm(), 'routes': routes})


def book_cab(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            fare = get_fare(booking.pickup_city, booking.drop_city, booking.cab_type)
            if booking.trip_type == 'round_trip':
                fare = int(fare * 1.9)
            booking.estimated_fare = fare
            booking.status = 'pending'
            booking.save()                                  # <-- this is where operational error was: table didn't exist
            return redirect('booking_success', booking_id=booking.booking_id)
        return render(request, 'cabs/book.html', {'form': form})
    initial = {}
    if request.GET.get('from'): initial['pickup_city'] = request.GET['from']
    if request.GET.get('to'):   initial['drop_city']   = request.GET['to']
    return render(request, 'cabs/book.html', {'form': BookingForm(initial=initial)})


def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    return render(request, 'cabs/booking_success.html', {'booking': booking})


def track_cab(request):
    booking, error = None, None
    tracking_allowed = False
    minutes_until_tracking = None

    if request.method == 'POST':
        form = TrackBookingForm(request.POST)
        if form.is_valid():
            try:
                booking = Booking.objects.get(
                    booking_id=form.cleaned_data['booking_id'].strip().upper(),
                    customer_phone=form.cleaned_data['customer_phone'].strip()
                )
                # Check if tracking is allowed (10 min before pickup)
                if booking.driver and booking.status in ['confirmed', 'on_trip']:
                    from datetime import datetime, date
                    pickup_dt = datetime.combine(booking.pickup_date, booking.pickup_time)
                    pickup_dt = timezone.make_aware(pickup_dt)
                    now = timezone.now()
                    diff_minutes = (pickup_dt - now).total_seconds() / 60

                    if booking.status == 'on_trip':
                        tracking_allowed = True
                    elif diff_minutes <= 10:
                        tracking_allowed = True
                    else:
                        tracking_allowed = False
                        minutes_until_tracking = int(diff_minutes - 10)

            except Booking.DoesNotExist:
                error = 'No booking found. Please check your Booking ID and phone number.'
    else:
        form = TrackBookingForm()

    return render(request, 'cabs/track.html', {
        'form': form,
        'booking': booking,
        'error': error,
        'tracking_allowed': tracking_allowed,
        'minutes_until_tracking': minutes_until_tracking,
    })


def get_fare_api(request):
    fare = get_fare(request.GET.get('pickup',''), request.GET.get('drop',''), request.GET.get('cab_type','sedan'))
    return JsonResponse({'fare': fare})


def get_cab_location(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    if booking.driver and booking.driver.current_lat:
        return JsonResponse({'status':'ok','lat':booking.driver.current_lat,'lng':booking.driver.current_lng,
            'driver_name':booking.driver.name,'vehicle_number':booking.driver.vehicle_number,'vehicle_model':booking.driver.vehicle_model})
    return JsonResponse({'status':'no_location'})


@csrf_exempt
def update_driver_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            d = Driver.objects.get(id=data.get('driver_id'))
            d.current_lat = data.get('lat'); d.current_lng = data.get('lng')
            d.last_location_update = timezone.now(); d.save()
            return JsonResponse({'status':'ok'})
        except Driver.DoesNotExist:
            return JsonResponse({'status':'error'},status=404)
    return JsonResponse({'status':'error'},status=400)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! We'll get back to you shortly.")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'cabs/contact.html', {'form': form})


def routes(request):
    route_list = [
        {'from':'Chandigarh','to':'Delhi',   'distance':'260 km','time':'4-5 hrs', 'sedan':2800,'suv':3800,'tempo':5500, 'highlights':'NH-44 via Ambala'},
        {'from':'Chandigarh','to':'Shimla',  'distance':'115 km','time':'2-3 hrs', 'sedan':1800,'suv':2500,'tempo':3800, 'highlights':'Scenic mountain route'},
        {'from':'Chandigarh','to':'Amritsar','distance':'230 km','time':'3-4 hrs', 'sedan':2000,'suv':2800,'tempo':4000, 'highlights':'Golden Temple city'},
        {'from':'Chandigarh','to':'Manali',  'distance':'310 km','time':'7-8 hrs', 'sedan':3500,'suv':4800,'tempo':7000, 'highlights':'Kullu Valley route'},
        {'from':'Chandigarh','to':'Jammu',   'distance':'195 km','time':'4-5 hrs', 'sedan':3000,'suv':4200,'tempo':6000, 'highlights':'Vaishno Devi base'},
        {'from':'Chandigarh','to':'Srinagar','distance':'635 km','time':'11-12 hrs','sedan':5500,'suv':7500,'tempo':11000,'highlights':'Banihal tunnel route'},
        {'from':'Chandigarh','to':'Jaipur',  'distance':'520 km','time':'8-9 hrs', 'sedan':5000,'suv':6800,'tempo':9500, 'highlights':'Pink City express'},
    ]
    return render(request, 'cabs/routes.html', {'route_list': route_list})
