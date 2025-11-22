from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum
from .models import Donor, BloodInventory, BloodRequest, Donation
from .forms import DonorForm, BloodRequestForm, DonationForm, PatientQRFilterForm
from django.contrib.auth import logout
from django.shortcuts import redirect
from .utils import (
    get_or_create_inventory,
    update_inventory_on_donation,
    update_inventory_on_issue,
    prioritize_donors_for_request,
    crossmatch_assistant,
)
from .notifications import send_email_notification, send_sms_notification


@login_required
def dashboard(request):
    donor_count = Donor.objects.count()
    total_units = BloodInventory.objects.aggregate(total=Sum('units_available'))['total'] or 0
    pending_requests = BloodRequest.objects.filter(status='PENDING').count()
    fulfilled_requests = BloodRequest.objects.filter(status='FULFILLED').count()

    inventory = get_or_create_inventory()
    donations_stats = Donation.objects.values('blood_group').annotate(total_units=Sum('units'))

    context = {
        'donor_count': donor_count,
        'total_units': total_units,
        'pending_requests': pending_requests,
        'fulfilled_requests': fulfilled_requests,
        'inventory': inventory,
        'donations_stats': donations_stats,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def donor_list(request):
    donors = Donor.objects.all().order_by('-created_at')
    return render(request, 'core/donor_list.html', {'donors': donors})

# core/views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.urls import reverse

def login_page(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember = request.POST.get("remember_me") == "on"

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            # handle session expiry
            if remember:
                request.session.set_expiry(60 * 60 * 24 * 14)  # 14 days
            else:
                request.session.set_expiry(0)  # until browser closes

            return redirect(request.POST.get("next") or "core:dashboard")
        else:
            error = "Invalid username or password"

    return render(request, "core/login.html", {
        "error": error,
        "next": request.GET.get("next"),
    })

def logout_page(request):
    logout(request)
    return redirect('/login')
def donor_create(request):
    if request.method == 'POST':
        form = DonorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Donor added successfully')
            #return redirect('core:donor_list')
    else:
        form = DonorForm()
    return render(request, 'core/donor_form.html', {'form': form})


@login_required
def donor_update(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    if request.method == 'POST':
        form = DonorForm(request.POST, instance=donor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Donor updated successfully')
            return redirect('core:donor_list')
    else:
        form = DonorForm(instance=donor)
    return render(request, 'core/donor_form.html', {'form': form})


@login_required
def donor_delete(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    if request.method == 'POST':
        donor.delete()
        messages.success(request, 'Donor deleted')
        return redirect('core:donor_list')
    return render(request, 'core/confirm_delete.html', {'object': donor, 'type': 'Donor'})


@login_required
def inventory_view(request):
    inventory = get_or_create_inventory()
    return render(request, 'core/inventory.html', {'inventory': inventory})


@login_required
def donation_create(request):
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save()
            donor = donation.donor
            donor.total_donations += 1
            donor.last_donation_date = donation.donation_date
            donor.reputation_points += 10
            donor.save()

            update_inventory_on_donation(donation)

            messages.success(request, 'Donation recorded and inventory updated.')
            return redirect('core:inventory')
    else:
        form = DonationForm()
    return render(request, 'core/donation_form.html', {'form': form})


@login_required
def request_list(request):
    requests = BloodRequest.objects.all().order_by('-created_at')
    return render(request, 'core/request_list.html', {'requests': requests})


def request_create(request):
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save()
            send_email_notification(
                to_email=getattr(request.user, 'email', None),
                subject=f"New Blood Request #{blood_request.id}",
                message=f"A new blood request has been created for {blood_request.blood_group} ({blood_request.units_requested} units).",
            )
            messages.success(request, 'Blood request created.')
            #return redirect('core:request_list')
    else:
        form = BloodRequestForm()
    return render(request, 'core/request_form.html', {'form': form})


@login_required
def request_detail(request, pk):
    blood_request = get_object_or_404(BloodRequest, pk=pk)
    recommended_donors = prioritize_donors_for_request(blood_request)
    inventory = BloodInventory.objects.filter(blood_group=blood_request.blood_group).first()
    return render(
        request,
        'core/request_detail.html',
        {
            'request_obj': blood_request,
            'recommended_donors': recommended_donors,
            'inventory': inventory,
        },
    )


@login_required
def assign_donors_to_request(request, pk):
    blood_request = get_object_or_404(BloodRequest, pk=pk)
    recommended_donors = prioritize_donors_for_request(blood_request)

    if request.method == 'POST':
        donor_ids = request.POST.getlist('donors')
        units_to_issue = int(request.POST.get('units_to_issue', blood_request.units_requested))

        if not update_inventory_on_issue(blood_request.blood_group, units_to_issue):
            messages.error(request, 'Not enough stock in inventory.')
            return redirect('core:request_detail', pk=blood_request.id)

        donors = Donor.objects.filter(id__in=donor_ids)
        blood_request.donors_assigned.set(donors)
        blood_request.status = 'FULFILLED'
        blood_request.save()

        for d in donors:
            sms_message = f"You are requested to donate blood ({d.blood_group}) for patient {blood_request.patient_name} at {blood_request.location}."
            send_sms_notification(d.phone, sms_message)
            send_email_notification(
                d.email,
                "Urgent Blood Donation Request",
                sms_message,
            )

        messages.success(request, 'Donors assigned and notified, inventory updated.')
        return redirect('core:request_detail', pk=blood_request.id)

    return render(
        request,
        'core/assign_donors.html',
        {
            'request_obj': blood_request,
            'recommended_donors': recommended_donors,
        },
    )


def patient_qr_view(request):
    form = PatientQRFilterForm(request.GET or None)
    donors = Donor.objects.filter(is_available=True)
    if form.is_valid():
        blood_group = form.cleaned_data.get('blood_group')
        city = form.cleaned_data.get('city')
        urgency = form.cleaned_data.get('urgency')

        if blood_group:
            donors = donors.filter(blood_group=blood_group)
        if city:
            donors = donors.filter(city__icontains=city)

    return render(request, 'core/patient_qr.html', {'form': form, 'donors': donors})


def donor_qr_view(request):
    steps = [
        "Check basic medical eligibility (age, weight, general health).",
        "Carry a valid ID proof to the donation center.",
        "Avoid heavy meals and alcohol before donating.",
        "Stay hydrated and take rest after donation.",
    ]
    centers = [
        {"name": "City Blood Bank", "address": "Main Road, City Center", "phone": "9999999999"},
        {"name": "Govt. Hospital Blood Center", "address": "Govt. Hospital Campus", "phone": "8888888888"},
    ]
    return render(request, 'core/donor_qr.html', {'steps': steps, 'centers': centers})


def crossmatch_api(request):
    patient_bg = request.GET.get('patient_bg')
    donor_bg = request.GET.get('donor_bg')
    if not patient_bg or not donor_bg:
        return JsonResponse({'error': 'patient_bg and donor_bg are required'}, status=400)

    result = crossmatch_assistant(patient_bg, donor_bg)
    return JsonResponse(result)
def donate(request):
    return render(request,'core/donate.html')
