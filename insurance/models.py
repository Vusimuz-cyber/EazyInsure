from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('user', 'User')], default='user')
    date_of_birth = models.DateField(null=True, blank=True)
    driving_experience_years = models.IntegerField(default=0)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    claims_history = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    proof_of_income = models.FileField(upload_to='income_proofs/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car_make = models.CharField(max_length=100)
    car_model = models.CharField(max_length=100)
    car_year = models.IntegerField()
    vin = models.CharField(max_length=17)
    registration_number = models.CharField(max_length=10)
    mileage = models.IntegerField()
    modifications = models.TextField(blank=True, null=True)
    has_tracking_device = models.BooleanField(default=False)
    has_alarm = models.BooleanField(default=False)
    parking_type = models.CharField(max_length=50, choices=[
        ('garage', 'Garage'), ('street', 'Street'), ('secure_lot', 'Secure Lot')
    ], default='street')
    full_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=13)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('declined', 'Declined')
    ], default='pending')
    decline_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car_make} {self.car_model} - {self.full_name}"

class VehicleInspection(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('declined', 'Declined')
    ], default='pending')
    decline_reason = models.TextField(blank=True, null=True)
    photo1 = models.ImageField(upload_to='inspections/', blank=True, null=True)
    photo2 = models.ImageField(upload_to='inspections/', blank=True, null=True)
    photo3 = models.ImageField(upload_to='inspections/', blank=True, null=True)
    photo4 = models.ImageField(upload_to='inspections/', blank=True, null=True)
    photo5 = models.ImageField(upload_to='inspections/', blank=True, null=True)
    photo6 = models.ImageField(upload_to='inspections/', blank=True, null=True)
    photo7 = models.ImageField(upload_to='inspections/', blank=True, null=True)
    photo8 = models.ImageField(upload_to='inspections/', blank=True, null=True)
    photo9 = models.ImageField(upload_to='inspections/', blank=True, null=True)
    photo10 = models.ImageField(upload_to='inspections/', blank=True, null=True)

    def __str__(self):
        return f"Inspection for {self.application}"

class Quote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car_make = models.CharField(max_length=100)
    car_model = models.CharField(max_length=100)
    car_year = models.IntegerField()
    address = models.TextField()
    has_tracking_device = models.BooleanField(default=False)
    has_alarm = models.BooleanField(default=False)
    parking_type = models.CharField(max_length=50, choices=[
        ('garage', 'Garage'), ('street', 'Street'), ('secure_lot', 'Secure Lot')
    ], default='street')
    premium = models.DecimalField(max_digits=10, decimal_places=2)
    risk_factors = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('declined', 'Declined')
    ], default='pending')
    decline_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote for {self.car_make} {self.car_model} - R{self.premium}"

class Policy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True)
    policy_type = models.CharField(max_length=50, choices=[
        ('third_party', 'Third-Party'),
        ('third_party_fire_theft', 'Third-Party, Fire & Theft'),
        ('comprehensive', 'Comprehensive')
    ])
    premium = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'), ('expired', 'Expired'), ('cancelled', 'Cancelled')
    ], default='active')
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed')
    ], default='pending')

    def __str__(self):
        return f"{self.policy_type} Policy for {self.user.username}"

class Claim(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, null=True)
    claim_type = models.CharField(max_length=100)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('declined', 'Declined')
    ], default='pending')
    decline_reason = models.TextField(blank=True, null=True)
    photo1 = models.ImageField(upload_to='claims/', blank=True, null=True)
    photo2 = models.ImageField(upload_to='claims/', blank=True, null=True)
    photo3 = models.ImageField(upload_to='claims/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Claim for {self.application} - {self.claim_type}"