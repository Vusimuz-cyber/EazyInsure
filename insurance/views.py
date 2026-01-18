from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, date
from .models import Application, VehicleInspection, UserProfile, Quote, Claim, Policy
import re

# High-risk vehicles and areas for quote calculation
HIGH_RISK_VEHICLES = [
    'Toyota Hilux', 'Toyota Fortuner', 'Volkswagen Polo', 'Ford Ranger',
    'Nissan NP200', 'Toyota Quantum', 'BMW 3 Series', 'Hyundai H-1',
    'Audi A3', 'Mercedes-Benz C-Class', 'Haval H6', 'Chery Tiggo'
]
HIGH_RISK_AREAS = [
    'Johannesburg CBD', 'Soweto', 'Midrand', 'Centurion', 'Eldorado Park',
    'Ivory Park', 'Moroka', 'Thembisa', 'Sandringham', 'Orange Farm',
    'Mariannhill', 'Umlazi', 'Umbilo', 'Nyanga', 'Delft', 'Philippi East', 'Harare'
]

# Authentication Views
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            profile, created = UserProfile.objects.get_or_create(user=user, defaults={'role': 'user'})
            if profile.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'user')
        date_of_birth = request.POST.get('date_of_birth')
        driving_experience_years = request.POST.get('driving_experience_years')
        license_number = request.POST.get('license_number')
        emergency_contact = request.POST.get('emergency_contact')

        if not all([username, email, password1, password2, date_of_birth, driving_experience_years, license_number, emergency_contact]):
            messages.error(request, 'All fields are required.')
            return render(request, 'register.html')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'register.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        UserProfile.objects.create(
            user=user,
            role=role,
            date_of_birth=date_of_birth,
            driving_experience_years=int(driving_experience_years),
            license_number=license_number,
            emergency_contact=emergency_contact
        )
        login(request, user)
        if role == 'admin':
            return redirect('admin_dashboard')
        return redirect('dashboard')
    return render(request, 'register.html')

def user_logout(request):
    logout(request)
    return redirect('login')

# User Dashboard Views
@login_required
def dashboard(request):
    applications = Application.objects.filter(user=request.user)
    claims = Claim.objects.filter(application__user=request.user)
    policies = Policy.objects.filter(user=request.user)
    quotes = Quote.objects.filter(user=request.user)
    context = {
        'applications': applications,
        'claims': claims,
        'policies': policies,
        'quotes': quotes,
    }
    return render(request, 'dashboard.html', context)

@login_required
def get_quote(request):
    if request.method == 'POST':
        car_make = request.POST.get('car_make')
        car_model = request.POST.get('car_model')
        car_year = request.POST.get('car_year')
        address = request.POST.get('address')
        has_tracking_device = request.POST.get('has_tracking_device') == 'on'
        has_alarm = request.POST.get('has_alarm') == 'on'
        parking_type = request.POST.get('parking_type')

        if not all([car_make, car_model, car_year, address, parking_type]):
            messages.error(request, 'All fields are required.')
            return render(request, 'get_quote.html')

        # Calculate base premium
        base_premium = 500.00
        risk_factors = []

        # Vehicle Risk
        vehicle_name = f"{car_make} {car_model}"
        vehicle_risk_factor = 1.5 if vehicle_name in HIGH_RISK_VEHICLES else 1.0
        if vehicle_risk_factor > 1:
            risk_factors.append(f"High-risk vehicle ({vehicle_name})")
        base_premium *= vehicle_risk_factor

        # Car Age Risk
        car_year = int(car_year)
        if car_year < 2010:
            base_premium *= 1.3
            risk_factors.append("Older vehicle (pre-2010)")

        # Location Risk
        location_risk_factor = 1.0
        for area in HIGH_RISK_AREAS:
            if area.lower() in address.lower():
                location_risk_factor = 1.4
                risk_factors.append(f"High-risk area ({area})")
                break
        base_premium *= location_risk_factor

        # Driver Risk (Age and Experience)
        user_profile = request.user.userprofile
        today = date.today()
        age = today.year - user_profile.date_of_birth.year - (
            (today.month, today.day) < (user_profile.date_of_birth.month, user_profile.date_of_birth.day)
        )
        driving_experience = user_profile.driving_experience_years

        age_risk_factor = 1.0
        if 18 <= age <= 25 or age >= 65:
            age_risk_factor = 1.3
            risk_factors.append("High-risk age group")
        elif 26 <= age <= 64:
            age_risk_factor = 0.9
        base_premium *= age_risk_factor

        experience_risk_factor = 1.0
        if driving_experience < 2:
            experience_risk_factor = 1.5
            risk_factors.append("Low driving experience (< 2 years)")
        elif 2 <= driving_experience <= 5:
            experience_risk_factor = 1.2
            risk_factors.append("Moderate driving experience (2-5 years)")
        base_premium *= experience_risk_factor

        # Security Features Discount
        security_discount = 1.0
        if has_tracking_device:
            security_discount -= 0.1
        if has_alarm:
            security_discount -= 0.05
        if parking_type == 'garage' or parking_type == 'secure_lot':
            security_discount -= 0.1
        base_premium *= security_discount
        if security_discount < 1.0:
            risk_factors.append("Security features applied (discount)")

        # Final Premium
        premium = max(base_premium, 300.00)  # Minimum premium
        risk_factors_str = "; ".join(risk_factors) if risk_factors else "No significant risk factors."

        Quote.objects.create(
            user=request.user,
            car_make=car_make,
            car_model=car_model,
            car_year=car_year,
            address=address,
            has_tracking_device=has_tracking_device,
            has_alarm=has_alarm,
            parking_type=parking_type,
            premium=premium,
            risk_factors=risk_factors_str,
        )
        messages.success(request, f'Quote generated: R{premium:.2f}. Check your dashboard for details.')
        return redirect('dashboard')
    return render(request, 'get_quote.html')

@login_required
def apply_insurance(request):
    if request.method == 'POST':
        car_make = request.POST.get('car_make')
        car_model = request.POST.get('car_model')
        car_year = request.POST.get('car_year')
        vin = request.POST.get('vin')
        registration_number = request.POST.get('registration_number')
        mileage = request.POST.get('mileage')
        modifications = request.POST.get('modifications')
        has_tracking_device = request.POST.get('has_tracking_device') == 'on'
        has_alarm = request.POST.get('has_alarm') == 'on'
        parking_type = request.POST.get('parking_type')
        full_name = request.POST.get('full_name')
        id_number = request.POST.get('id_number')
        address = request.POST.get('address')
        proof_of_income = request.FILES.get('proof_of_income')

        if not all([car_make, car_model, car_year, vin, registration_number, mileage, parking_type, full_name, id_number, address]):
            messages.error(request, 'All fields are required.')
            return render(request, 'apply_insurance.html')

        # Validate VIN (17 characters, alphanumeric)
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
            messages.error(request, 'Invalid VIN number.')
            return render(request, 'apply_insurance.html')

        # Validate Registration Number (e.g., ABC123GP)
        if not re.match(r'^[A-Z0-9]{6,10}$', registration_number):
            messages.error(request, 'Invalid registration number.')
            return render(request, 'apply_insurance.html')

        # Validate ID Number (13 digits)
        if not re.match(r'^\d{13}$', id_number):
            messages.error(request, 'ID number must be 13 digits.')
            return render(request, 'apply_insurance.html')

        application = Application.objects.create(
            user=request.user,
            car_make=car_make,
            car_model=car_model,
            car_year=car_year,
            vin=vin,
            registration_number=registration_number,
            mileage=int(mileage),
            modifications=modifications,
            has_tracking_device=has_tracking_device,
            has_alarm=has_alarm,
            parking_type=parking_type,
            full_name=full_name,
            id_number=id_number,
            address=address,
        )
        request.user.userprofile.proof_of_income = proof_of_income
        request.user.userprofile.save()
        messages.success(request, 'Application submitted successfully.')
        return redirect('dashboard')
    return render(request, 'apply_insurance.html')

@login_required
def inspections(request):
    applications = Application.objects.filter(user=request.user, status='pending')
    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        application = Application.objects.get(id=application_id, user=request.user)
        photos = [request.FILES.get(f'photo{i}') for i in range(1, 11)]
        if all(photos):
            inspection = VehicleInspection.objects.create(application=application)
            for i, photo in enumerate(photos, 1):
                setattr(inspection, f'photo{i}', photo)
            inspection.save()
            messages.success(request, 'Inspection submitted successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'All 10 photos are required.')
    return render(request, 'inspections.html', {'applications': applications})

@login_required
def submit_claim(request):
    applications = Application.objects.filter(user=request.user, status='approved')
    policies = Policy.objects.filter(user=request.user, status='active')
    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        policy_id = request.POST.get('policy_id')
        claim_type = request.POST.get('claim_type')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        photos = [request.FILES.get(f'photo{i}') for i in range(1, 4)]
        if not all([application_id, policy_id, claim_type, description, amount]):
            messages.error(request, 'All fields are required.')
            return render(request, 'submit_claim.html', {'applications': applications, 'policies': policies})
        try:
            amount = float(amount)
        except ValueError:
            messages.error(request, 'Amount must be a valid number.')
            return render(request, 'submit_claim.html', {'applications': applications, 'policies': policies})
        application = Application.objects.get(id=application_id, user=request.user)
        policy = Policy.objects.get(id=policy_id, user=request.user)
        claim = Claim.objects.create(
            application=application,
            policy=policy,
            claim_type=claim_type,
            description=description,
            amount=amount,
        )
        for i, photo in enumerate(photos, 1):
            if photo:
                setattr(claim, f'photo{i}', photo)
        claim.save()
        messages.success(request, 'Claim submitted successfully.')
        return redirect('dashboard')
    return render(request, 'submit_claim.html', {'applications': applications, 'policies': policies})

# Policy Management Views
@login_required
def view_policies(request):
    policies = Policy.objects.filter(user=request.user)
    quotes = Quote.objects.filter(user=request.user, status='approved')
    applications = Application.objects.filter(user=request.user, status='approved')
    if request.method == 'POST':
        quote_id = request.POST.get('quote_id')
        application_id = request.POST.get('application_id')
        policy_type = request.POST.get('policy_type')
        quote = Quote.objects.get(id=quote_id, user=request.user)
        application = Application.objects.get(id=application_id, user=request.user)

        # Calculate premium based on policy type
        premium = float(quote.premium)
        if policy_type == 'third_party':
            premium *= 0.8
        elif policy_type == 'third_party_fire_theft':
            premium *= 1.0
        elif policy_type == 'comprehensive':
            premium *= 1.2

        # Create policy
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=365)
        Policy.objects.create(
            user=request.user,
            application=application,
            policy_type=policy_type,
            premium=premium,
            start_date=start_date,
            end_date=end_date,
        )
        messages.success(request, 'Policy created successfully. Please make payment to activate.')
        return redirect('view_policies')
    return render(request, 'view_policies.html', {'policies': policies, 'quotes': quotes, 'applications': applications})

@login_required
def pay_policy(request, policy_id):
    policy = get_object_or_404(Policy, id=policy_id, user=request.user)
    if request.method == 'POST':
        # Simulate payment processing
        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        cvv = request.POST.get('cvv')

        if not all([card_number, expiry_date, cvv]):
            messages.error(request, 'All payment fields are required.')
            return render(request, 'pay_policy.html', {'policy': policy})

        # Basic card validation
        if not re.match(r'^\d{16}$', card_number):
            messages.error(request, 'Invalid card number.')
            return render(request, 'pay_policy.html', {'policy': policy})
        if not re.match(r'^(0[1-9]|1[0-2])/(\d{2})$', expiry_date):
            messages.error(request, 'Invalid expiry date (MM/YY).')
            return render(request, 'pay_policy.html', {'policy': policy})
        if not re.match(r'^\d{3}$', cvv):
            messages.error(request, 'Invalid CVV.')
            return render(request, 'pay_policy.html', {'policy': policy})

        # Simulate successful payment
        policy.payment_status = 'paid'
        policy.status = 'active'
        policy.save()
        messages.success(request, 'Payment successful. Policy is now active.')
        return redirect('view_policies')
    return render(request, 'pay_policy.html', {'policy': policy})

@login_required
def renew_policy(request, policy_id):
    policy = get_object_or_404(Policy, id=policy_id, user=request.user)
    if request.method == 'POST':
        # Extend policy by 1 year
        policy.end_date += timedelta(days=365)
        policy.status = 'active'
        policy.payment_status = 'pending'
        policy.save()
        messages.success(request, 'Policy renewed successfully. Please make payment to activate.')
        return redirect('view_policies')
    return render(request, 'renew_policy.html', {'policy': policy})

# Admin Dashboard Views
@login_required
def admin_dashboard(request):
    if request.user.userprofile.role != 'admin':
        return redirect('dashboard')
    total_users = User.objects.count()
    total_quotes = Quote.objects.count()
    total_applications = Application.objects.count()
    total_inspections = VehicleInspection.objects.count()
    total_claims = Claim.objects.count()
    total_policies = Policy.objects.count()
    high_risk_vehicles = Application.objects.filter(
        car_make__in=[v.split()[0] for v in HIGH_RISK_VEHICLES]
    ).count()
    high_risk_areas = Application.objects.filter(
        address__icontains='Johannesburg'
    ).count()  # Simplified for demo
    policies_third_party = Policy.objects.filter(policy_type='third_party').count()
    policies_third_party_fire_theft = Policy.objects.filter(policy_type='third_party_fire_theft').count()
    policies_comprehensive = Policy.objects.filter(policy_type='comprehensive').count()
    context = {
        'total_users': total_users,
        'total_quotes': total_quotes,
        'total_applications': total_applications,
        'total_inspections': total_inspections,
        'total_claims': total_claims,
        'total_policies': total_policies,
        'high_risk_vehicles': high_risk_vehicles,
        'high_risk_areas': high_risk_areas,
        'policies_third_party': policies_third_party,
        'policies_third_party_fire_theft': policies_third_party_fire_theft,
        'policies_comprehensive': policies_comprehensive,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def manage_quotes(request):
    if request.user.userprofile.role != 'admin':
        return redirect('dashboard')
    quotes = Quote.objects.all()
    if request.method == 'POST':
        quote_id = request.POST.get('quote_id')
        action = request.POST.get('action')
        quote = Quote.objects.get(id=quote_id)
        if action == 'approve':
            quote.status = 'approved'
        elif action == 'decline':
            quote.status = 'declined'
            quote.decline_reason = request.POST.get('decline_reason', '')
        quote.save()
        messages.success(request, f'Quote {action}d successfully.')
    return render(request, 'manage_quotes.html', {'quotes': quotes})

@login_required
def manage_applications(request):
    if request.user.userprofile.role != 'admin':
        return redirect('dashboard')
    applications = Application.objects.all()
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        action = request.POST.get('action')
        application = Application.objects.get(id=app_id)
        if action == 'approve':
            application.status = 'approved'
        elif action == 'decline':
            application.status = 'declined'
            application.decline_reason = request.POST.get('decline_reason', '')
        application.save()
        messages.success(request, f'Application {action}d successfully.')
    return render(request, 'manage_applications.html', {'applications': applications})

@login_required
def manage_inspections(request):
    if request.user.userprofile.role != 'admin':
        return redirect('dashboard')
    inspections = VehicleInspection.objects.all()
    if request.method == 'POST':
        inspection_id = request.POST.get('inspection_id')
        action = request.POST.get('action')
        inspection = VehicleInspection.objects.get(id=inspection_id)
        if action == 'approve':
            inspection.status = 'approved'
        elif action == 'decline':
            inspection.status = 'declined'
            inspection.decline_reason = request.POST.get('decline_reason', '')
        inspection.save()
        messages.success(request, f'Inspection {action}d successfully.')
    return render(request, 'manage_inspections.html', {'inspections': inspections})

@login_required
def manage_claims(request):
    if request.user.userprofile.role != 'admin':
        return redirect('dashboard')
    claims = Claim.objects.all()
    if request.method == 'POST':
        claim_id = request.POST.get('claim_id')
        action = request.POST.get('action')
        claim = Claim.objects.get(id=claim_id)
        if action == 'approve':
            claim.status = 'approved'
        elif action == 'decline':
            claim.status = 'declined'
            claim.decline_reason = request.POST.get('decline_reason', '')
        claim.save()
        messages.success(request, f'Claim {action}d successfully.')
    return render(request, 'manage_claims.html', {'claims': claims})