from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='staff_dashboard'),
    path('reservation/<int:reservation_id>/', views.reservation_detail, name='staff_reservation_detail'),
    path('verify-payment/<int:payment_id>/', views.verify_payment, name='verify_payment'),
    path('update-status/<int:reservation_id>/', views.update_reservation_status, name='update_reservation_status'),
    path('rooms/', views.room_management, name='room_management'),
]
