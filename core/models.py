from django.db import models
from django.utils import timezone

BLOOD_GROUP_CHOICES = [
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
]

URGENCY_CHOICES = [
    ('LOW', 'Low'),
    ('MEDIUM', 'Medium'),
    ('HIGH', 'High'),
    ('CRITICAL', 'Critical'),
]

REQUEST_STATUS = [
    ('PENDING', 'Pending'),
    ('PARTIAL', 'Partially Fulfilled'),
    ('FULFILLED', 'Fulfilled'),
    ('CANCELLED', 'Cancelled'),
]


class Donor(models.Model):
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100, default="")
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    last_donation_date = models.DateField(blank=True, null=True)
    total_donations = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    reputation_points = models.PositiveIntegerField(default=0)
    badges = models.CharField(max_length=255, blank=True, help_text="Comma separated badge names")
    responsiveness_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.blood_group})"

    @property
    def is_eligible(self):
        if not self.last_donation_date:
            return True
        delta = timezone.now().date() - self.last_donation_date
        return delta.days >= 90


class BloodInventory(models.Model):
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, unique=True)
    units_available = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.blood_group}: {self.units_available} units"


class Donation(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    units = models.PositiveIntegerField()
    donation_date = models.DateField(default=timezone.now)
    is_urgent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.donor.name} - {self.units} units ({self.blood_group})"


class BloodRequest(models.Model):
    requester_type = models.CharField(max_length=50, default='Hospital')  # or 'Individual'
    requester_name = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField(blank=True, null=True)
    hospital_name = models.CharField(max_length=255, blank=True, null=True)
    patient_name = models.CharField(max_length=255)
    patient_age = models.PositiveIntegerField(blank=True, null=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    units_requested = models.PositiveIntegerField()
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='MEDIUM')
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    donors_assigned = models.ManyToManyField(Donor, blank=True, related_name='assigned_requests')

    def __str__(self):
        return f"Request #{self.id} - {self.blood_group} ({self.status})"


class NotificationLog(models.Model):
    recipient = models.CharField(max_length=255)
    channel = models.CharField(max_length=20)  # email / sms / dashboard
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='SENT')

    def __str__(self):
        return f"{self.recipient} via {self.channel} at {self.created_at}"
