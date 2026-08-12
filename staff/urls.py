from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='staff_dashboard'),
    path('reservation/<int:reservation_id>/', views.reservation_detail, name='staff_reservation_detail'),
    path('verify-payment/<int:payment_id>/', views.verify_payment, name='verify_payment'),
    path('update-status/<int:reservation_id>/', views.update_reservation_status, name='update_reservation_status'),
    path('reservation/<int:reservation_id>/delete/', views.delete_reservation, name='delete_reservation'),
    path('rooms/', views.room_management, name='room_management'),

    # Gestión de usuarios (solo superusuario)
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]
