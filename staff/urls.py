from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='staff_dashboard_root'),
    path('dashboard/', views.dashboard, name='staff_dashboard'),
    path('reservation/<int:reservation_id>/', views.reservation_detail, name='staff_reservation_detail'),
    path('verify-payment/<int:payment_id>/', views.verify_payment, name='verify_payment'),
    path('update-status/<int:reservation_id>/', views.update_reservation_status, name='update_reservation_status'),
    path('reservation/<int:reservation_id>/delete/', views.delete_reservation, name='delete_reservation'),
    path('rooms/', views.room_management, name='room_management'),

    # Spa/Gym service management
    path('service/<int:reservation_id>/', views.service_reservation_detail, name='staff_service_detail'),
    path('verify-service-payment/<int:payment_id>/', views.verify_service_payment, name='verify_service_payment'),
    path('update-service-status/<int:reservation_id>/', views.update_service_status, name='update_service_status'),
    path('service/<int:reservation_id>/delete/', views.delete_service_reservation, name='delete_service_reservation'),
    path('event/<int:inquiry_id>/read/', views.mark_event_read, name='mark_event_read'),
    path('event/create/', views.create_event_inquiry_staff, name='create_event_inquiry_staff'),
    path('event/<int:inquiry_id>/delete/', views.delete_event_inquiry, name='delete_event_inquiry'),

    # Gestión de usuarios (solo superusuario)
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),

    # Auditoría (solo superusuario)
    path('audit/', views.audit_log_view, name='audit_log'),

    # Respaldo y Restauración (solo superusuario)
    path('backup/', views.backup_database, name='backup_restore'),
    path('backup/download/<str:filename>/', views.download_backup, name='download_backup'),
    path('backup/delete/<str:filename>/', views.delete_backup, name='delete_backup'),
    path('backup/restore/', views.restore_database, name='restore_database'),

    # Manual de uso (todo el staff)
    path('manual/', views.user_manual, name='user_manual'),
]
