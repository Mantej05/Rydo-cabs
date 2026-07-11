from django import forms
from .models import Booking, ContactMessage, CITY_CHOICES, CAB_TYPE_CHOICES
from django.utils import timezone


class BookingForm(forms.ModelForm):
    pickup_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
    )
    pickup_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
    )
    return_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = Booking
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'pickup_city', 'drop_city', 'pickup_date', 'pickup_time',
            'cab_type', 'passengers', 'trip_type', 'return_date',
        ]
        widgets = {
            'passengers': forms.NumberInput(attrs={'min': 1, 'max': 12}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pickup = cleaned_data.get('pickup_city')
        drop = cleaned_data.get('drop_city')
        if pickup and drop and pickup == drop:
            raise forms.ValidationError("Pickup and drop cities cannot be the same.")
        trip_type = cleaned_data.get('trip_type')
        return_date = cleaned_data.get('return_date')
        if trip_type == 'round_trip' and not return_date:
            raise forms.ValidationError("Please select a return date for round trip.")
        return cleaned_data


class TrackBookingForm(forms.Form):
    booking_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Rydo-AB1234'}),
        label='Booking ID'
    )
    customer_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '+91 XXXXX XXXXX'}),
        label='Registered Phone Number'
    )


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }
