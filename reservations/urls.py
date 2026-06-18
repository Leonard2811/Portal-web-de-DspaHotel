from django.urls import path
from . import views

urlpatterns = [
    path('booking/', views.booking, name='booking'),
    path('create/', views.create_reservation, name='create_reservation'),
    path('upload-payment/<int:reservation_id>/', views.upload_payment, name='upload_payment'),
    path('confirmation/<int:reservation_id>/', views.reservation_confirmation, name='reservation_confirmation'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('cancel/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
]
