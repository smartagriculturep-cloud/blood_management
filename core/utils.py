from django.utils import timezone
from .models import Donor, BloodRequest, BloodInventory, BLOOD_GROUP_CHOICES


def get_or_create_inventory():
    for bg, _ in BLOOD_GROUP_CHOICES:
        BloodInventory.objects.get_or_create(blood_group=bg)
    return BloodInventory.objects.all()


def update_inventory_on_donation(donation):
    inv, _ = BloodInventory.objects.get_or_create(blood_group=donation.blood_group)
    inv.units_available += donation.units
    inv.save()


def update_inventory_on_issue(blood_group, units):
    inv, _ = BloodInventory.objects.get_or_create(blood_group=blood_group)
    if inv.units_available >= units:
        inv.units_available -= units
        inv.save()
        return True
    return False


def calculate_donor_score(donor: Donor, request: BloodRequest) -> float:
    score = 0.0

    if donor.blood_group == request.blood_group:
        score += 50

    if donor.is_eligible:
        score += 20
    else:
        score -= 20

    if donor.is_available:
        score += 10
    else:
        score -= 30

    score += min(donor.total_donations * 2, 20)
    score += min(donor.responsiveness_score, 20)
    score += min(donor.reputation_points / 10, 20)

    if donor.city and request.location:
        if donor.city.lower() == request.location.lower():
            score += 15
        elif donor.city.split()[0].lower() in request.location.lower():
            score += 5

    if donor.last_donation_date:
        days = (timezone.now().date() - donor.last_donation_date).days
        if days < 90:
            score -= 40

    return score


def prioritize_donors_for_request(request: BloodRequest, limit=20):
    donors = Donor.objects.filter(blood_group=request.blood_group, is_available=True)
    scored = [(d, calculate_donor_score(d, request)) for d in donors]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [d for d, s in scored[:limit] if s > 0]


COMPATIBILITY = {
    'O-': ['O-'],
    'O+': ['O+', 'O-'],
    'A-': ['A-', 'O-'],
    'A+': ['A+', 'A-', 'O+', 'O-'],
    'B-': ['B-', 'O-'],
    'B+': ['B+', 'B-', 'O+', 'O-'],
    'AB-': ['AB-', 'A-', 'B-', 'O-'],
    'AB+': ['AB+', 'AB-', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-'],
}


def crossmatch_assistant(patient_bg: str, donor_bg: str):
    safe_donors = COMPATIBILITY.get(patient_bg, [])
    is_compatible = donor_bg in safe_donors

    explanation = ""
    if is_compatible:
        explanation = (
            f"Donor blood group {donor_bg} is compatible with patient blood group {patient_bg}. "
            "This match follows standard ABO and Rh compatibility rules."
        )
    else:
        explanation = (
            f"Donor blood group {donor_bg} is NOT compatible with patient blood group {patient_bg} "
            "under standard ABO and Rh rules. Choose another donor or consult a transfusion specialist."
        )

    complexity_flag = False
    if patient_bg.startswith('AB') and donor_bg not in safe_donors:
        complexity_flag = True

    return {
        'is_compatible': is_compatible,
        'complexity_flag': complexity_flag,
        'explanation': explanation,
    }
