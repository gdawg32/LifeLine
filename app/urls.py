from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('donors_signup/', views.donors_signup, name='donors_signup'),
    path('donors_login/', views.donors_login, name='donors_login'),
    path('staff_login/', views.staff_login, name='staff_login'),
    path('staff_portal/', views.staff_portal, name='staff_portal'),
    path('logout/', views.logout_view, name='logout'),
    path('donors_portal/', views.donors_portal, name='donors_portal'),
    path('book_appointment/', views.book_appointment, name='book_appointment'),
    path('cancel_appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('staff_portal/appointments/<str:date>/', views.get_appointments, name='get_appointments'),
    path('staff_portal/add_donation/<int:appointment_id>/', views.add_donation, name='add_donation'),
    path('staff_portal/add_recipient/', views.add_recipient, name='add_recipient'),
    path('request_blood/', views.request_blood, name='request_blood'),
    path('view_blood_request/', views.view_blood_request, name='view_blood_request'),
    path('add_blood_request_to_recipient/<int:request_id>/', views.add_blood_request_to_recipient, name='add_blood_request_to_recipient'),
    path('download_certificate/<int:donation_id>/', views.download_certificate, name='download_certificate'),

]