from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Donor, Appointment, Donation, Recipient
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime
from django.db.models import Sum

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def donors_signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        blood_type = request.POST.get('blood_type')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        address = request.POST.get('address')
        password = request.POST.get('password')

        # Create the user
        user = User.objects.create_user(username=email, password=password, first_name=first_name, last_name=last_name, email=email)
        group = Group.objects.get(name='donors')
        user.groups.add(group)
        user.save()

        # Create the donor
        donor = Donor(
            user=user,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            blood_type=blood_type,
            phone_number=phone_number,
            address=address
        )
        donor.save()

        return HttpResponse('Donor Saved Successfully')

    return render(request, 'donors_signup.html')

def donors_login(request):

    if request.user.is_authenticated and request.user.groups.filter(name='donors').exists():
        return redirect('donors_portal')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('donors_portal')
        else:
            # Invalid login
            return HttpResponse('Invalid login')

    return render(request, 'donors_login.html')

def staff_login(request):
    if request.user.is_authenticated and request.user.groups.filter(name='staff').exists():
        return redirect('staff_portal')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        username = User.objects.get(email=email).username
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('staff_portal')
        else:
            # Invalid login
            return HttpResponse('Invalid login')

    return render(request, 'staff_login.html')

@login_required
def staff_portal(request):
    donors = Donor.objects.all()
    donations = Donation.objects.all()
    for donation in donations:
        donation.total_volume = donation.used_volume + donation.volume
    recipients = Recipient.objects.all()
    blood_stock = Donation.objects.values('donor__blood_type').annotate(total_volume=Sum('volume')).order_by('donor__blood_type')
    context = {
        'donors': donors,
        'donations': donations,
        'blood_stock': blood_stock,
        'recipients': recipients
    }
    return render(request, 'staff_portal.html', context)

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def donors_portal(request):
    donor = Donor.objects.get(user=request.user)
    donations = Donation.objects.filter(donor=donor)
    for donation in donations:
        donation.total_volume = donation.used_volume + donation.volume
    upcoming_appointments = Appointment.objects.filter(donor=donor, appointment_date__gte=datetime.date.today())
    context = {
        'donor': donor,
        'upcoming_appointments': upcoming_appointments,
        'donations': donations
    }

    return render(request, 'donors_portal.html', context)

@login_required
def edit_profile(request):
    donor = Donor.objects.get(user=request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        blood_type = request.POST.get('blood_type')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        email = request.POST.get('email')
        
        user = User.objects.get(username=request.user.username)
        user.first_name = first_name
        user.last_name = last_name
        donor.date_of_birth = date_of_birth
        donor.gender = gender
        donor.blood_type = blood_type
        donor.phone_number = phone_number
        donor.address = address
        user.email = email

        user.save()
        donor.save()
        return redirect('donors_portal')

@login_required
def book_appointment(request):
    if request.method == 'POST':
        donor = request.user.donor
        appointment_date = request.POST.get('date')
        appointment_time = request.POST.get('time')

        # Create and save the appointment
        Appointment.objects.create(
            donor=donor,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        )

        # Add a success message
        messages.success(request, 'Appointment booked successfully!')

        # Redirect back to the same page
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('index')

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    appointment.delete()
    messages.success(request, 'Appointment canceled successfully!')
    return redirect(request.META.get('HTTP_REFERER', '/'))

def get_appointments(request, date):
    appointments = Appointment.objects.filter(appointment_date=date).select_related('donor').order_by('appointment_time')
    appointments_data = [
        {   
            'id': appointment.id,
            'donor': f'{appointment.donor.first_name} {appointment.donor.last_name}',
            'time': appointment.appointment_time.strftime('%H:%M')
        }
        for appointment in appointments
    ]
    return JsonResponse(appointments_data, safe=False)

@login_required
def add_donation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        print(request.POST)
        volume = float(request.POST.get('volume'))
        # Create the donation record
        donation = Donation.objects.create(
            donor=appointment.donor,
            date_of_donation=appointment.appointment_date,
            volume=volume
            )
        donation.save()
        appointment.delete()

        messages.success(request, 'Donation added successfully!')
        # Redirect to the appointment list or another appropriate page
        return redirect('staff_portal')
@login_required
def add_recipient(request):
    if request.method == 'POST':
        # Get the form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        blood_type = request.POST.get('blood_type')
        required_volume = float(request.POST.get('volume'))

        # Get donations of the same blood type
        donations = Donation.objects.filter(donor__blood_type=blood_type).order_by('date_of_donation')

        total_available_volume = 0
        selected_donations = []

        # Check if enough volume is available across multiple donations
        for donation in donations:
            available_volume = donation.volume - donation.used_volume
            if total_available_volume >= required_volume:
                break
            if available_volume > 0:
                selected_donations.append(donation)
                total_available_volume += available_volume

        if total_available_volume < required_volume:
            messages.error(request, "Not enough matching blood type available.")
            return redirect('staff_portal')  # Redirect to an appropriate page

        remaining_volume = required_volume
        for donation in selected_donations:
            available_volume = donation.volume - donation.used_volume
            if remaining_volume <= 0:
                break
            if available_volume >= remaining_volume:
                donation.used_volume += remaining_volume
                donation.volume -= remaining_volume  # Subtract the used volume
                remaining_volume = 0
            else:
                donation.used_volume += available_volume
                donation.volume -= available_volume  # Subtract the entire available volume
                remaining_volume -= available_volume
            donation.save()

        # Create the recipient and link the donations to them
        recipient = Recipient.objects.create(
            first_name=first_name,
            last_name=last_name,
            blood_type=blood_type,
            date_of_birth=request.POST.get('date_of_birth'),
            gender=request.POST.get('gender'),
            phone_number=request.POST.get('phone_number'),
            volume = required_volume,
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            hospital=request.POST.get('hospital'),
        )

        # Success message
        messages.success(request, f"Recipient {first_name} {last_name} added successfully!")

        return redirect('staff_portal')  # Redirect to an appropriate page


