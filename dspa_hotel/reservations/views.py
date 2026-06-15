from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Customer, Reservation, PaymentProof
from core.models import Room
from datetime import datetime


@login_required
def booking(request):
    """Vista principal de reservación con búsqueda de disponibilidad"""
    today = datetime.now().date()
    rooms = Room.objects.filter(is_active=True)

    # Pre-fill from query params
    room_id = request.GET.get('room_id')
    service_type = request.GET.get('service_type', 'room')
    selected_room = None
    if room_id:
        selected_room = Room.objects.filter(id=room_id).first()

    context = {
        'today': today.strftime('%Y-%m-%d'),
        'rooms': rooms,
        'selected_room': selected_room,
        'service_type': service_type,
        'service_choices': Reservation.SERVICE_CHOICES,
    }
    return render(request, 'reservations/booking.html', context)


@login_required
def create_reservation(request):
    """Crear una nueva reservación"""
    if request.method == 'POST':
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            messages.warning(request, 'Debe completar su perfil antes de reservar.')
            return redirect('complete_profile')

        service_type = request.POST.get('service_type', 'room')
        room_id = request.POST.get('room_id')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        adults = int(request.POST.get('adults', 1))
        children = int(request.POST.get('children', 0))
        special_requests = request.POST.get('special_requests', '')

        room = None
        if room_id and service_type == 'room':
            room = Room.objects.filter(id=room_id).first()

        if check_in and check_out:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
            nights = (check_out_date - check_in_date).days

            if nights <= 0:
                messages.error(request, 'La fecha de salida debe ser posterior a la fecha de entrada.')
                return redirect('booking')

            if room:
                total_price = room.price_per_night * nights
            else:
                total_price = 0

            reservation = Reservation.objects.create(
                customer=customer,
                service_type=service_type,
                room=room,
                check_in=check_in_date,
                check_out=check_out_date,
                adults_count=adults,
                children_count=children,
                total_price=total_price,
                special_requests=special_requests,
                status='pending',
            )

            messages.success(request, f'Reservación #{reservation.id} creada exitosamente.')
            return redirect('upload_payment', reservation_id=reservation.id)
        else:
            messages.error(request, 'Debe seleccionar fechas válidas.')
            return redirect('booking')

    return redirect('booking')


@login_required
def upload_payment(request, reservation_id):
    """Subir comprobante de pago"""
    reservation = get_object_or_404(Reservation, id=reservation_id, customer__user=request.user)

    if request.method == 'POST':
        amount = request.POST.get('amount', reservation.total_price)
        proof_image = request.FILES.get('proof_image')

        if proof_image:
            PaymentProof.objects.create(
                reservation=reservation,
                amount=amount,
                proof_image=proof_image,
            )
            reservation.status = 'payment_uploaded'
            reservation.save()
            messages.success(request, 'Comprobante subido exitosamente. Será verificado por nuestro equipo.')
            return redirect('reservation_confirmation', reservation_id=reservation.id)
        else:
            messages.error(request, 'Debe adjuntar el comprobante de pago.')

    context = {
        'reservation': reservation,
    }
    return render(request, 'reservations/upload_payment.html', context)


@login_required
def reservation_confirmation(request, reservation_id):
    """Confirmación de reservación"""
    reservation = get_object_or_404(Reservation, id=reservation_id, customer__user=request.user)
    payments = reservation.payments.all()
    context = {
        'reservation': reservation,
        'payments': payments,
    }
    return render(request, 'reservations/confirmation.html', context)


@login_required
def my_reservations(request):
    """Historial de reservaciones del cliente"""
    try:
        customer = Customer.objects.get(user=request.user)
        reservations = Reservation.objects.filter(customer=customer).order_by('-created_at')
    except Customer.DoesNotExist:
        reservations = []

    context = {
        'reservations': reservations,
    }
    return render(request, 'reservations/my_reservations.html', context)


@login_required
def cancel_reservation(request, reservation_id):
    """Cancelar una reservación"""
    try:
        customer = Customer.objects.get(user=request.user)
        reservation = get_object_or_404(Reservation, id=reservation_id, customer=customer)
        if reservation.status in ['pending', 'payment_uploaded']:
            reservation.status = 'cancelled'
            reservation.save()
            messages.success(request, f'Reservación #{reservation.id} cancelada.')
        else:
            messages.error(request, 'No se puede cancelar esta reservación.')
    except Customer.DoesNotExist:
        messages.error(request, 'Perfil no encontrado.')

    return redirect('my_reservations')
