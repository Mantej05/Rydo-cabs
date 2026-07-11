from django.urls import path
from . import views

urlpatterns = [
    path('',                views.home,                   name='home'),
    path('book/',           views.book_cab,               name='book_cab'),
    path('booking/success/<str:booking_id>/', views.booking_success, name='booking_success'),
    path('track/',          views.track_cab,              name='track_cab'),
    path('routes/',         views.routes,                 name='routes'),
    path('contact/',        views.contact,                name='contact'),
    path('api/fare/',       views.get_fare_api,           name='get_fare_api'),
    path('api/cab/location/<str:booking_id>/', views.get_cab_location, name='get_cab_location'),
    path('api/driver/location/update/', views.update_driver_location, name='update_driver_location'),
]
