from django.urls import path
from . import views

urlpatterns = [
    path('booking/', views.booking, name='booking'),
    path('create/', views.create_reservation, name='create_reservation'),
    path('upload-payment/<int:reservation_id>/', views.upload_payment, name='upload_payment'),
    path('confirmation/<int:reservation_id>/', views.reservation_confirmation, name='reservation_confirmation'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('cancel/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),

    # Spa & Gym Booking
    path('spa-booking/', views.spa_booking, name='spa_booking'),
    path('gym-booking/', views.gym_booking, name='gym_booking'),
    path('create-service/', views.create_service_reservation, name='create_service_reservation'),
    path('upload-service-payment/<int:reservation_id>/', views.upload_service_payment, name='upload_service_payment'),
    path('service-confirmation/<int:reservation_id>/', views.service_reservation_confirmation, name='service_reservation_confirmation'),
    path('cancel-service/<int:reservation_id>/', views.cancel_service_reservation, name='cancel_service_reservation'),

    # Event Inquiry
    path('event-inquiry/', views.event_inquiry, name='event_inquiry'),
]
