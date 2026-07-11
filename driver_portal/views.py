from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.contrib import messages
from datetime import date, timedelta

from cabs.models import Booking, Driver, BOOKING_STATUS


# ── helpers ──────────────────────────────────────────────────────────────────
def _is_admin(user):
    return user.is_staff or user.is_superuser

def _get_driver(user):
    try:
        return user.driver
    except Exception:
        return None

def _time_ago(dt):
    s = int((timezone.now() - dt).total_seconds())
    if s < 60:   return f"{s}s ago"
    if s < 3600: return f"{s//60}m ago"
    return f"{s//3600}h ago"


# ── auth ─────────────────────────────────────────────────────────────────────
def portal_login(request):
    if request.user.is_authenticated:
        return redirect('portal_dashboard')
    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username',''), password=request.POST.get('password',''))
        if user:
            if _is_admin(user) or _get_driver(user):
                login(request, user)
                return redirect('portal_dashboard')
            else:
                error = 'You do not have portal access.'
        else:
            error = 'Invalid credentials or no portal access.'
    return render(request, 'driver_portal/login.html', {'error': error})

def portal_logout(request):
    logout(request)
    return redirect('portal_login')

# ── dashboard ─────────────────────────────────────────────────────────────────
@login_required(login_url='portal_login')
def dashboard(request):
    today  = date.today()
    driver = _get_driver(request.user)
    admin  = _is_admin(request.user)

    today_completed = Booking.objects.filter(created_at__date=today, status='completed')
    today_revenue   = today_completed.aggregate(Sum('estimated_fare'))['estimated_fare__sum'] or 0
    today_commission = sum(b.admin_commission() for b in today_completed)

    all_completed  = Booking.objects.filter(status='completed')
    total_revenue  = all_completed.aggregate(Sum('estimated_fare'))['estimated_fare__sum'] or 0

    pending_bookings = Booking.objects.filter(status='pending').order_by('-created_at')

    # 7-day chart
    chart_labels, chart_revenue = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rev = Booking.objects.filter(created_at__date=d, status='completed').aggregate(Sum('estimated_fare'))['estimated_fare__sum'] or 0
        chart_labels.append(d.strftime('%d %b'))
        chart_revenue.append(float(rev))

    my_bookings = None
    if driver and not admin:
        my_bookings = Booking.objects.filter(driver=driver).order_by('-created_at')[:8]

    return render(request, 'driver_portal/dashboard.html', {
        'is_admin': admin, 'driver': driver, 'today': today,
        'today_revenue': today_revenue, 'today_commission': today_commission,
        'today_count': today_completed.count(),
        'total_bookings': Booking.objects.count(),
        'pending_count': Booking.objects.filter(status='pending').count(),
        'completed_count': Booking.objects.filter(status='completed').count(),
        'total_revenue': total_revenue,
        'pending_bookings': pending_bookings,
        'chart_labels': chart_labels,
        'chart_revenue': chart_revenue,
        'my_bookings': my_bookings,
    })


# ── bookings table ────────────────────────────────────────────────────────────
@login_required(login_url='portal_login')
def all_bookings(request):
    driver = _get_driver(request.user)
    admin  = _is_admin(request.user)

    qs = Booking.objects.select_related('driver').order_by('-created_at')
    status_f = request.GET.get('status','')
    date_f   = request.GET.get('date','')
    search   = request.GET.get('search','')
    if status_f: qs = qs.filter(status=status_f)
    if date_f:   qs = qs.filter(pickup_date=date_f)
    if search:
        qs = qs.filter(Q(booking_id__icontains=search)|Q(customer_name__icontains=search)|Q(customer_phone__icontains=search))
    if driver and not admin:
        qs = qs.filter(Q(driver=driver)|Q(status='pending'))

    available_drivers = Driver.objects.filter(is_available=True, is_active=True)
    return render(request, 'driver_portal/bookings.html', {
        'bookings': qs, 'is_admin': admin, 'driver': driver,
        'status_choices': BOOKING_STATUS, 'status_filter': status_f,
        'date_filter': date_f, 'search': search,
        'available_drivers': available_drivers,
    })


# ── accept (driver clicks Accept on a pending ride) ───────────────────────────
@login_required(login_url='portal_login')
def accept_booking(request, booking_id):
    driver = _get_driver(request.user)
    if not driver:
        messages.error(request, 'Only drivers can accept bookings.')
        return redirect('portal_bookings')
    booking = get_object_or_404(Booking, booking_id=booking_id, status='pending')
    booking.driver      = driver
    booking.status      = 'confirmed'
    booking.accepted_at = timezone.now()
    booking.save()
    driver.is_available = False
    driver.save()
    messages.success(request, f'Booking {booking_id} accepted! Customer: {booking.customer_name} | {booking.customer_phone}')
    return redirect('portal_bookings')


# ── update status ─────────────────────────────────────────────────────────────
@login_required(login_url='portal_login')
def update_status(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    driver  = _get_driver(request.user)
    admin   = _is_admin(request.user)
    if not admin and (not driver or booking.driver != driver):
        messages.error(request, 'Permission denied.')
        return redirect('portal_bookings')
    new_status = request.POST.get('status','')
    if new_status in dict(BOOKING_STATUS):
        booking.status = new_status
        if new_status == 'completed':
            booking.completed_at = timezone.now()
            if booking.driver:
                booking.driver.is_available = True
                booking.driver.save()
        booking.save()
        messages.success(request, f'Status updated to {new_status}.')
    return redirect('portal_bookings')


# ── assign driver (admin) ─────────────────────────────────────────────────────
@login_required(login_url='portal_login')
def assign_driver(request, booking_id):
    if not _is_admin(request.user):
        messages.error(request, 'Admin only action.')
        return redirect('portal_bookings')
    booking = get_object_or_404(Booking, booking_id=booking_id)
    if request.method == 'POST':
        try:
            drv = Driver.objects.get(id=request.POST.get('driver_id'))
            booking.driver = drv; booking.status = 'confirmed'
            booking.accepted_at = timezone.now(); booking.save()
            messages.success(request, f'Driver {drv.name} assigned to {booking_id}.')
        except Driver.DoesNotExist:
            messages.error(request, 'Driver not found.')
    return redirect('portal_bookings')


# ── drivers list (admin) ──────────────────────────────────────────────────────
@login_required(login_url='portal_login')
def drivers_list(request):
    if not _is_admin(request.user):
        return redirect('portal_dashboard')
    drivers = Driver.objects.annotate(
        total_completed=Count('booking', filter=Q(booking__status='completed')),
        total_earned=Sum('booking__estimated_fare', filter=Q(booking__status='completed')),
    ).order_by('-total_completed')
    return render(request, 'driver_portal/drivers.html', {'drivers': drivers, 'is_admin': True})


# ── revenue page (admin) ──────────────────────────────────────────────────────
@login_required(login_url='portal_login')
def revenue(request):
    if not _is_admin(request.user):
        return redirect('portal_dashboard')
    today = date.today()

    def _stats(qs):
        total  = qs.aggregate(Sum('estimated_fare'))['estimated_fare__sum'] or 0
        comm   = sum(b.admin_commission() for b in qs)
        return float(total), float(comm), qs.count()

    t_total, t_comm, t_cnt = _stats(Booking.objects.filter(created_at__date=today, status='completed'))
    m_total, m_comm, m_cnt = _stats(Booking.objects.filter(created_at__year=today.year, created_at__month=today.month, status='completed'))
    a_total, a_comm, a_cnt = _stats(Booking.objects.filter(status='completed'))

    driver_rev = Driver.objects.annotate(
        rides=Count('booking', filter=Q(booking__status='completed')),
        earned=Sum('booking__estimated_fare', filter=Q(booking__status='completed')),
    ).filter(rides__gt=0).order_by('-earned')

    daily = []
    for i in range(29,-1,-1):
        d = today - timedelta(days=i)
        rev = Booking.objects.filter(created_at__date=d,status='completed').aggregate(Sum('estimated_fare'))['estimated_fare__sum'] or 0
        daily.append({'date': d.strftime('%d %b'), 'revenue': float(rev)})

    return render(request, 'driver_portal/revenue.html', {
        'is_admin': True,
        't_total': t_total, 't_comm': t_comm, 't_driver': t_total - t_comm, 't_cnt': t_cnt,
        'm_total': m_total, 'm_comm': m_comm, 'm_cnt': m_cnt,
        'a_total': a_total, 'a_comm': a_comm, 'a_cnt': a_cnt,
        'driver_rev': driver_rev, 'daily': daily,
    })


# ── polling API for live alerts ───────────────────────────────────────────────
@login_required(login_url='portal_login')
def pending_api(request):
    qs = Booking.objects.filter(status='pending').order_by('-created_at')
    data = [{
        'booking_id': b.booking_id, 'customer_name': b.customer_name,
        'customer_phone': b.customer_phone, 'pickup_city': b.pickup_city,
        'drop_city': b.drop_city, 'pickup_date': str(b.pickup_date),
        'pickup_time': str(b.pickup_time), 'cab_type': b.get_cab_type_display(),
        'passengers': b.passengers, 'fare': str(b.estimated_fare or 0),
        'ago': _time_ago(b.created_at),
    } for b in qs]
    return JsonResponse({'pending': data, 'count': len(data)})
