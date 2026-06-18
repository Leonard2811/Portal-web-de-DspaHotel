from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from reservations.models import Reservation, PaymentProof, Customer
from core.models import Room
from .models import StaffProfile
from datetime import datetime, date


def staff_required(view_func):
    """Decorador para verificar que el usuario es staff"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_staff or hasattr(request.user, 'staffprofile')):
            messages.error(request, 'No tiene permisos para acceder a esta sección.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_required
def dashboard(request):
    """Dashboard principal del staff"""
    today = date.today()

    # Estadísticas generales
    total_reservations = Reservation.objects.count()
    pending_reservations = Reservation.objects.filter(status='pending').count()
    payment_uploaded = Reservation.objects.filter(status='payment_uploaded').count()
    confirmed_reservations = Reservation.objects.filter(status='confirmed').count()
    cancelled_reservations = Reservation.objects.filter(status='cancelled').count()
    completed_reservations = Reservation.objects.filter(status='completed').count()

    # Ingresos
    total_income = Reservation.objects.filter(
        status__in=['confirmed', 'completed']
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Habitaciones
    total_rooms = Room.objects.filter(is_active=True).count()
    available_rooms = Room.objects.filter(is_active=True, status='available').count()
    occupied_rooms = Room.objects.filter(is_active=True, status='occupied').count()
    maintenance_rooms = Room.objects.filter(is_active=True, status='maintenance').count()

    # Check-ins y check-outs del día
    todays_checkins = Reservation.objects.filter(
        check_in=today,
        status__in=['confirmed', 'payment_uploaded']
    )
    todays_checkouts = Reservation.objects.filter(
        check_out=today,
        status='confirmed'
    )

    # Comprobantes pendientes
    pending_payments = PaymentProof.objects.filter(verification_status='pending').order_by('-payment_date')

    # Todas las reservaciones
    all_reservations = Reservation.objects.select_related('customer__user', 'room').all().order_by('-created_at')

    # Filtros
    status_filter = request.GET.get('status', '')
    service_filter = request.GET.get('service', '')
    if status_filter:
        all_reservations = all_reservations.filter(status=status_filter)
    if service_filter:
        all_reservations = all_reservations.filter(service_type=service_filter)

    context = {
        'total_reservations': total_reservations,
        'pending_reservations': pending_reservations,
        'payment_uploaded': payment_uploaded,
        'confirmed_reservations': confirmed_reservations,
        'cancelled_reservations': cancelled_reservations,
        'completed_reservations': completed_reservations,
        'total_income': total_income,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'maintenance_rooms': maintenance_rooms,
        'todays_checkins': todays_checkins,
        'todays_checkouts': todays_checkouts,
        'pending_payments': pending_payments,
        'all_reservations': all_reservations,
        'status_filter': status_filter,
        'service_filter': service_filter,
        'status_choices': Reservation.STATUS_CHOICES,
        'service_choices': Reservation.SERVICE_CHOICES,
    }
    return render(request, 'staff/dashboard.html', context)


@staff_required
def reservation_detail(request, reservation_id):
    """Detalle completo de una reservación"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    payments = reservation.payments.all().order_by('-payment_date')

    context = {
        'reservation': reservation,
        'payments': payments,
    }
    return render(request, 'staff/reservation_details.html', context)


@staff_required
def verify_payment(request, payment_id):
    """Verificar o rechazar un comprobante de pago"""
    payment = get_object_or_404(PaymentProof, id=payment_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('staff_notes', '')
        payment.staff_notes = notes

        if action == 'verify':
            payment.verification_status = 'verified'
            payment.save()
            payment.reservation.status = 'confirmed'
            payment.reservation.save()
            if payment.reservation.room:
                payment.reservation.room.status = 'reserved'
                payment.reservation.room.save()
            messages.success(request, f'Pago verificado. Reservación #{payment.reservation.id} confirmada.')
        elif action == 'reject':
            payment.verification_status = 'rejected'
            payment.save()
            payment.reservation.status = 'pending'
            payment.reservation.save()
            messages.warning(request, f'Pago rechazado para Reservación #{payment.reservation.id}.')

        return redirect('staff_reservation_detail', reservation_id=payment.reservation.id)

    context = {
        'payment': payment,
        'reservation': payment.reservation,
    }
    return render(request, 'staff/verify_payment.html', context)


@staff_required
def update_reservation_status(request, reservation_id):
    """Actualizar estado de una reservación"""
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Reservation.STATUS_CHOICES):
            old_status = reservation.status
            reservation.status = new_status
            reservation.save()

            # Actualizar estado de habitación si aplica
            if reservation.room:
                if new_status == 'confirmed':
                    reservation.room.status = 'reserved'
                elif new_status == 'completed' or new_status == 'cancelled':
                    reservation.room.status = 'available'
                reservation.room.save()

            messages.success(request, f'Reservación #{reservation.id} actualizada de {old_status} a {new_status}.')

    return redirect('staff_reservation_detail', reservation_id=reservation.id)


@staff_required
def room_management(request):
    """Gestión de habitaciones"""
    rooms = Room.objects.all().order_by('room_type', 'room_number')

    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        new_status = request.POST.get('status')
        room = get_object_or_404(Room, id=room_id)
        room.status = new_status
        room.save()
        messages.success(request, f'Habitación {room.room_number} actualizada a {room.get_status_display()}.')

    context = {'rooms': rooms}
    return render(request, 'staff/room_management.html', context)
