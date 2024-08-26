from django.db import models
from django.contrib.auth.models import User

class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    donor_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.TextField()
    blood_type = models.TextField()
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Donation(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    date_of_donation = models.DateField()
    volume = models.IntegerField()  # Volume in ml
    used_volume = models.IntegerField(default=0)  # Volume used in transfusions

    @property
    def available_volume(self):
        return self.volume - self.used_volume

    def __str__(self):
        return f"Donation by {self.donor} on {self.date_of_donation}"


class Recipient(models.Model):
    recipient_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.TextField()
    blood_type = models.TextField()
    volume = models.FloatField()
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    hospital = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Appointment(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    def __str__(self):
        return f"Appointment for {self.donor} on {self.appointment_date} at {self.appointment_time}"


class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    position = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

