from django import forms
from .models import Donor, BloodRequest, Donation, BLOOD_GROUP_CHOICES, URGENCY_CHOICES
from datetime import date


# Helper: Apply Bootstrap form-control class to all fields
def apply_bootstrap_widgets(fields):
    for field in fields:
        if not isinstance(fields[field].widget, forms.CheckboxInput):
            fields[field].widget.attrs.update({'class': 'form-control'})
        else:
            fields[field].widget.attrs.update({'class': 'form-check-input'})
    return fields


class DonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = [
            'name', 'age', 'phone', 'email', 'address', 'city',
            'blood_group', 'last_donation_date', 'is_available'
        ]
        widgets = {
            'last_donation_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['donor', 'blood_group', 'units', 'donation_date', 'is_urgent']
        widgets = {
            'donation_date': forms.DateInput(
                attrs={'type': 'date', 'value': date.today()}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)


class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = [
            'requester_type', 'requester_name', 'contact_phone',
            'contact_email', 'hospital_name', 'patient_name',
            'patient_age', 'blood_group', 'units_requested',
            'urgency', 'location', 'notes'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)


class PatientQRFilterForm(forms.Form):
    blood_group = forms.ChoiceField(
        choices=[('', 'Any')] + BLOOD_GROUP_CHOICES,
        required=False
    )
    city = forms.CharField(required=False)
    urgency = forms.ChoiceField(
        choices=[('', 'Any')] + URGENCY_CHOICES,
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_widgets(self.fields)
