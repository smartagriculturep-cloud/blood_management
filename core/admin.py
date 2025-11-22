from django.contrib import admin
from .models import Donor, BloodInventory, BloodRequest, Donation, NotificationLog


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('name', 'blood_group', 'city', 'is_available', 'total_donations', 'reputation_points')
    search_fields = ('name', 'phone', 'city', 'blood_group')
    list_filter = ('blood_group', 'city', 'is_available')


@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ('blood_group', 'units_available')


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_name', 'blood_group', 'units_requested', 'urgency', 'status', 'created_at')
    list_filter = ('blood_group', 'urgency', 'status')
    search_fields = ('patient_name', 'hospital_name', 'requester_name')


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'blood_group', 'units', 'donation_date', 'is_urgent')
    list_filter = ('blood_group', 'is_urgent')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'channel', 'subject', 'created_at', 'status')
    list_filter = ('channel', 'status')
