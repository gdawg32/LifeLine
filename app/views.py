from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Donor, Appointment, Donation, Recipient, BloodRequest
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime
from django.db.models import Sum
from django.utils import timezone
import io
from django.http import FileResponse, Http404
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime

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

        return redirect('donors_login')

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
    upcoming_appointments = Appointment.objects.filter(donor=donor, appointment_date__gte=datetime.now())
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
        recipient_blood_type = request.POST.get('blood_type')
        required_volume = float(request.POST.get('volume'))

        # Define blood type compatibility
        blood_type_compatibility = {
            'O-': ['O-'],
            'O+': ['O-', 'O+'],
            'A-': ['O-', 'A-'],
            'A+': ['O-', 'O+', 'A-', 'A+'],
            'B-': ['O-', 'B-'],
            'B+': ['O-', 'O+', 'B-', 'B+'],
            'AB-': ['O-', 'A-', 'B-', 'AB-'],
            'AB+': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+']
        }

        # Get donations of compatible blood types
        compatible_blood_types = blood_type_compatibility.get(recipient_blood_type, [])
        donations = Donation.objects.filter(donor__blood_type__in=compatible_blood_types).order_by('date_of_donation')

        total_available_volume = 0
        selected_donations = []

        # Check if enough volume is available across multiple donations without mixing blood types
        for donation in donations:
            if donation.donor.blood_type != recipient_blood_type and selected_donations:
                # Don't mix blood types
                continue
            available_volume = donation.volume - donation.used_volume
            if total_available_volume >= required_volume:
                break
            if available_volume > 0:
                selected_donations.append(donation)
                total_available_volume += available_volume

        if total_available_volume < required_volume:
            messages.error(request, "Not enough compatible blood type available.")
            return redirect('staff_portal')

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
            blood_type=recipient_blood_type,
            date_of_birth=request.POST.get('date_of_birth'),
            gender=request.POST.get('gender'),
            phone_number=request.POST.get('phone_number'),
            volume=required_volume,
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            hospital=request.POST.get('hospital'),
        )

        # Success message
        messages.success(request, f"Recipient {first_name} {last_name} added successfully!")

        return redirect('staff_portal')
    
def request_blood(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        blood_type = request.POST.get('blood_type')
        volume = float(request.POST.get('volume'))
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        address = request.POST.get('address')
        hospital = request.POST.get('hospital')
        needed_by = request.POST.get('needed_by')
        urgency_level = request.POST.get('urgency')

        try:
            # Create BloodRequest
            blood_request = BloodRequest.objects.create(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                gender=gender,
                blood_type=blood_type,
                volume=volume,
                phone_number=phone_number,
                email=email,
                address=address,
                hospital=hospital,
                needed_by=needed_by,
                urgency_level=urgency_level,
                status='Pending'
            )
            blood_request.save()

            # Success message
            messages.success(request, 'Your blood request has been submitted successfully!')
            return redirect('index')  # Reload the same page to display the modal

        except Exception as e:
            # Error handling
            messages.error(request, 'Something went wrong. Please try again.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
def view_blood_request(request):
    current_time = timezone.localtime()
    blood_requests = BloodRequest.objects.filter(needed_by__gte=current_time.date()).exclude(status='Processed')
    return JsonResponse({'blood_requests': list(blood_requests.values())})

@login_required
def add_blood_request_to_recipient(request, request_id):
    # Fetch the blood request using the request_id
    blood_request = get_object_or_404(BloodRequest, request_id=request_id)
    
    if request.method == 'POST':
        # Get the blood request data
        first_name = blood_request.first_name
        last_name = blood_request.last_name
        recipient_blood_type = blood_request.blood_type
        required_volume = blood_request.volume

        # Define blood type compatibility
        blood_type_compatibility = {
            'O-': ['O-'],
            'O+': ['O-', 'O+'],
            'A-': ['O-', 'A-'],
            'A+': ['O-', 'O+', 'A-', 'A+'],
            'B-': ['O-', 'B-'],
            'B+': ['O-', 'O+', 'B-', 'B+'],
            'AB-': ['O-', 'A-', 'B-', 'AB-'],
            'AB+': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+']
        }

        # Get donations of compatible blood types
        compatible_blood_types = blood_type_compatibility.get(recipient_blood_type, [])
        donations = Donation.objects.filter(donor__blood_type__in=compatible_blood_types).order_by('date_of_donation')

        total_available_volume = 0
        selected_donations = []

        # Check if enough volume is available across multiple donations without mixing blood types
        for donation in donations:
            if donation.donor.blood_type != recipient_blood_type and selected_donations:
                # Don't mix blood types
                continue
            available_volume = donation.volume - donation.used_volume
            if total_available_volume >= required_volume:
                break
            if available_volume > 0:
                selected_donations.append(donation)
                total_available_volume += available_volume

        if total_available_volume < required_volume:
            messages.error(request, "Not enough compatible blood type available.")
            return redirect('staff_portal')

        remaining_volume = required_volume
        for donation in selected_donations:
            available_volume = donation.volume - donation.used_volume
            if remaining_volume <= 0:
                break
            if available_volume >= remaining_volume:
                donation.used_volume += remaining_volume
                remaining_volume = 0
            else:
                donation.used_volume += available_volume
                remaining_volume -= available_volume
            donation.save()

        # Create the recipient from the blood request data
        recipient = Recipient.objects.create(
            first_name=first_name,
            last_name=last_name,
            blood_type=recipient_blood_type,
            date_of_birth=blood_request.date_of_birth,
            gender=blood_request.gender,
            phone_number=blood_request.phone_number,
            volume=required_volume,
            email=blood_request.email,
            address=blood_request.address,
            hospital=blood_request.hospital,
        )

        # Update the blood request status to 'Processed'
        blood_request.status = 'Processed'
        blood_request.save()

        recipient.save()

        # Success message
        messages.success(request, f"Recipient {first_name} {last_name} added successfully!")

        return redirect('staff_portal')

def generate_custom_certificate_with_template(donor_name, donation_date, template_path):
    # Create a BytesIO buffer to hold the PDF in memory
    buffer = io.BytesIO()

    # Create the PDF canvas using BytesIO as the file handle
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Load the JPG template as the background
    background = ImageReader(template_path)
    c.drawImage(background, 0, 0, width=width, height=height)

    # Donor's Name
    c.setFont("Helvetica-Bold", 42)
    c.setFillColorRGB(0, 0, 0)  # Black text for the name
    c.drawCentredString(width / 2, height - 290, donor_name)

    # Donation Date
    c.setFont("Helvetica", 24)
    c.setFillColorRGB(0, 0, 0)  # Black text for the name
    c.drawString(140, 155, donation_date)

    # Save the PDF to the buffer
    c.save()

    # Move the buffer's file pointer to the beginning
    buffer.seek(0)

    return buffer

@login_required
def download_certificate(request, donation_id):
    try:
        # Get the donation record using the donation_id
        donation = Donation.objects.get(id=donation_id)
    except Donation.DoesNotExist:
        raise Http404("Donation not found")

    # Get donor details
    donor_name = donation.donor.first_name + ' ' + donation.donor.last_name  # Assuming the donor has a 'name' field
    donation_date = donation.date_of_donation.strftime('%d-%m-%Y')

    # Path to the template image
    template_path = 'app/Template.png'

    # Generate the certificate PDF
    pdf_buffer = generate_custom_certificate_with_template(donor_name, donation_date, template_path)

    # Return the PDF as a response
    return FileResponse(pdf_buffer, as_attachment=True, filename=f"{donor_name}_certificate.pdf")
