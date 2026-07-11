# Rydo – Full Django Project

## Two Sites in One Project

| Site | URL | For |
|---|---|---|
| Customer Website | http://127.0.0.1:8000/ | Public – book cabs, track rides |
| Driver/Admin Portal | http://127.0.0.1:8000/portal/ | Private – drivers & admins only |
| Django Admin | http://127.0.0.1:8000/admin/ | Add drivers, manage data |

---

## Setup (Run These Commands in Order)

```bash
# 1. Install Django
pip install django

# 2. Run migrations (fixes the OperationalError)
python manage.py migrate

# 3. Create a superuser (admin login)
python manage.py createsuperuser

# 4. Start the server
python manage.py runserver
```

---

## How to Add Drivers (Step by Step)

1. Go to http://127.0.0.1:8000/admin/
2. Login with your superuser credentials
3. Click **Auth > Users > Add User** → create a username/password for the driver
4. Go to **Cabs > Drivers > Add Driver**
5. Link the User you just created, fill in name, phone, vehicle details
6. That driver can now login at http://127.0.0.1:8000/portal/

---

## How the Alert System Works

1. Customer books a ride on the website → booking saved as **Pending**
2. Every 10 seconds, the portal polls `/portal/api/pending/`
3. A **bell notification** appears + browser notification fires for all logged-in drivers
4. First driver to click **Accept** gets the ride → status changes to **Confirmed**
5. The alert disappears for all other drivers automatically
6. Driver updates status: Confirmed → On Trip → Completed

---

## Portal Features

### Dashboard
- Live pending ride alerts with sound + browser notification
- Today's stats: revenue, commission, ride count
- 7-day revenue bar chart

### Bookings Page
- Full table of all bookings with filters (status, date, search)
- Drivers can accept pending rides
- Admin can assign drivers manually
- Update status: Confirmed → On Trip → Completed → Cancelled

### Drivers Page (Admin only)
- All drivers with Driver ID, vehicle, completed rides, earnings

### Revenue Page (Admin only)
- Today / This Month / All Time revenue summary
- Rydo commission (15%) vs driver payout (85%)
- 30-day revenue line chart
- Per-driver earnings breakdown

---

## Project Structure

```
Rydo/
├── manage.py
├── settings.py
├── project_urls.py          ← routes / to cabs, /portal/ to driver_portal
├── cabs/                    ← Customer website app
│   ├── models.py            ← Booking, Driver, ContactMessage
│   ├── views.py             ← Customer-facing views
│   ├── forms.py             ← BookingForm, TrackForm, ContactForm
│   ├── urls.py
│   └── admin.py
├── driver_portal/           ← Driver & Admin portal app
│   ├── views.py             ← Dashboard, bookings, drivers, revenue, alerts API
│   └── urls.py
├── templates/
│   ├── cabs/                ← Customer site templates
│   └── driver_portal/       ← Portal templates (login, dashboard, bookings, drivers, revenue)
└── static/
    ├── css/style.css        ← Customer site CSS
    └── css/portal.css       ← Portal CSS
```
