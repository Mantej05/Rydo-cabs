from django.urls import path
from . import views

urlpatterns = [
    path('login/',                           views.portal_login,    name='portal_login'),
    path('logout/',                          views.portal_logout,   name='portal_logout'),
    path('',                                 views.dashboard,       name='portal_dashboard'),
    path('bookings/',                        views.all_bookings,    name='portal_bookings'),
    path('bookings/accept/<str:booking_id>/',  views.accept_booking,  name='portal_accept'),
    path('bookings/status/<str:booking_id>/',  views.update_status,   name='portal_update_status'),
    path('bookings/assign/<str:booking_id>/',  views.assign_driver,   name='portal_assign_driver'),
    path('drivers/',                         views.drivers_list,    name='portal_drivers'),
    path('revenue/',                         views.revenue,         name='portal_revenue'),
    path('api/pending/',                     views.pending_api,     name='portal_pending_api'),
]
