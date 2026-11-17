from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.db.models import Count, Sum, Q
from reservations.models import Reservation, PaymentProof, Customer, ServiceReservation, ServicePaymentProof, EventInquiry
from core.models import Room
from .models import StaffProfile, AuditLog
from datetime import datetime, date
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.templatetags.static import static
from email.mime.image import MIMEImage
import os
import shutil
from pathlib import Path

def log_audit(request, action, description):
    """Registrar una acción en el historial de auditoría"""
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        description=description,
        ip_address=ip or None,
    )


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


def _is_recepcionista(user):
    """Retorna True si el usuario es solo recepcionista (solo lectura)"""
    if user.is_superuser:
        return False
    if user.groups.filter(name='Encargados de Reservaciones').exists():
        return False
    if user.groups.filter(name='Recepcionistas de Datos').exists():
        return True
    # Si no tiene grupo, tratar como solo lectura
    return not user.is_superuser


def _is_operador_aqua(user):
    """Retorna True si el usuario es Operador Aqua Spa Gym"""
    if user.is_superuser:
        return False
    return user.groups.filter(name='Operadores Aqua Spa Gym').exists()


def can_edit_required(view_func):
    """Decorador: bloquea a recepcionistas de hacer cambios"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if _is_recepcionista(request.user):
            messages.error(request, 'No tienes permisos para realizar esta acción. Tu rol es solo de lectura.')
            return redirect('staff_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def superuser_required(view_func):
    """Decorador: solo superusuarios o miembros de Super Administradores pueden acceder"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_superuser or request.user.groups.filter(name='Super Administradores').exists()):
            messages.error(request, 'Solo el administrador principal puede realizar esta acción.')
            return redirect('staff_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_edit_services_required(view_func):
    """Decorador: permite a operadores Aqua y superiores editar servicios"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if _is_recepcionista(request.user):
            messages.error(request, 'No tienes permisos para realizar esta acción.')
            return redirect('staff_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_required
def dashboard(request):
    """Dashboard principal del staff"""
    today = date.today()
    mode = request.GET.get('mode', 'rooms')

    # Si es operador Aqua, forzar modo spa_gym
    if _is_operador_aqua(request.user):
        mode = 'spa_gym'

    # Estadísticas generales de HABITACIONES
    total_reservations = Reservation.objects.count()
    pending_reservations = Reservation.objects.filter(status='pending').count()
    payment_uploaded = Reservation.objects.filter(status='payment_uploaded').count()
    confirmed_reservations = Reservation.objects.filter(status='confirmed').count()
    cancelled_reservations = Reservation.objects.filter(status='cancelled').count()
    completed_reservations = Reservation.objects.filter(status='completed').count()

    # Ingresos habitaciones
    total_income = Reservation.objects.filter(
        status__in=['confirmed', 'completed']
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Habitaciones
    total_rooms = Room.objects.filter(is_active=True).count()
    available_rooms = Room.objects.filter(is_active=True, status='available').count()
    available_web = Room.objects.filter(is_active=True, status='available', sales_channel='web').count()
    available_door = Room.objects.filter(is_active=True, status='available', sales_channel='puerta').count()
    
    occupied_rooms = Room.objects.filter(is_active=True, status='occupied').count()
    occupied_web = Room.objects.filter(is_active=True, status='occupied', sales_channel='web').count()
    occupied_door = Room.objects.filter(is_active=True, status='occupied', sales_channel='puerta').count()
    
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

    # Comprobantes pendientes (habitaciones)
    pending_payments = PaymentProof.objects.filter(verification_status='pending').order_by('-payment_date')

    # Todas las reservaciones de habitaciones
    all_reservations = Reservation.objects.select_related('customer__user', 'room').all().order_by('-created_at')

    # Filtros para habitaciones
    status_filter = request.GET.get('status', '')
    service_filter = request.GET.get('service', '')
    if status_filter:
        all_reservations = all_reservations.filter(status=status_filter)
    if service_filter:
        all_reservations = all_reservations.filter(service_type=service_filter)

    # ========== ESTADÍSTICAS SPA/GYM ==========
    spa_total = ServiceReservation.objects.filter(service_category='spa').count()
    spa_pending = ServiceReservation.objects.filter(service_category='spa', status='pending').count()
    spa_uploaded = ServiceReservation.objects.filter(service_category='spa', status='payment_uploaded').count()
    spa_confirmed = ServiceReservation.objects.filter(service_category='spa', status='confirmed').count()
    spa_cancelled = ServiceReservation.objects.filter(service_category='spa', status='cancelled').count()
    
    gym_total = ServiceReservation.objects.filter(service_category='gym').count()
    gym_pending = ServiceReservation.objects.filter(service_category='gym', status='pending').count()
    gym_uploaded = ServiceReservation.objects.filter(service_category='gym', status='payment_uploaded').count()
    gym_confirmed = ServiceReservation.objects.filter(service_category='gym', status='confirmed').count()
    gym_cancelled = ServiceReservation.objects.filter(service_category='gym', status='cancelled').count()
    
    service_total = spa_total + gym_total
    service_pending = spa_pending + gym_pending
    service_uploaded = spa_uploaded + gym_uploaded
    service_confirmed = spa_confirmed + gym_confirmed
    service_cancelled = spa_cancelled + gym_cancelled
    
    service_income = ServiceReservation.objects.filter(
        status__in=['confirmed', 'completed']
    ).aggregate(total=Sum('price'))['total'] or 0

    # Comprobantes pendientes de servicios
    pending_service_payments = ServicePaymentProof.objects.filter(verification_status='pending').order_by('-payment_date')

    # Todas las reservaciones de servicios
    all_service_reservations = ServiceReservation.objects.select_related('customer__user').all().order_by('-created_at')

    # Filtros para servicios
    svc_status_filter = request.GET.get('svc_status', '')
    svc_cat_filter = request.GET.get('svc_cat', '')
    if svc_status_filter:
        all_service_reservations = all_service_reservations.filter(status=svc_status_filter)
    if svc_cat_filter:
        all_service_reservations = all_service_reservations.filter(service_category=svc_cat_filter)

    # Consultas de eventos
    event_inquiries = EventInquiry.objects.all().order_by('-created_at')
    total_event_inquiries = event_inquiries.count()
    unread_events = event_inquiries.filter(is_read=False).count()

    context = {
        'mode': mode,
        'is_operador_aqua': _is_operador_aqua(request.user),
        # Habitaciones
        'total_reservations': total_reservations,
        'pending_reservations': pending_reservations,
        'payment_uploaded': payment_uploaded,
        'confirmed_reservations': confirmed_reservations,
        'cancelled_reservations': cancelled_reservations,
        'completed_reservations': completed_reservations,
        'total_income': total_income,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'available_web': available_web,
        'available_door': available_door,
        'occupied_rooms': occupied_rooms,
        'occupied_web': occupied_web,
        'occupied_door': occupied_door,
        'maintenance_rooms': maintenance_rooms,
        'todays_checkins': todays_checkins,
        'todays_checkouts': todays_checkouts,
        'pending_payments': pending_payments,
        'all_reservations': all_reservations,
        'status_filter': status_filter,
        'service_filter': service_filter,
        'status_choices': Reservation.STATUS_CHOICES,
        'service_choices': Reservation.SERVICE_CHOICES,
        # Spa/Gym
        'spa_total': spa_total,
        'spa_pending': spa_pending,
        'spa_uploaded': spa_uploaded,
        'spa_confirmed': spa_confirmed,
        'spa_cancelled': spa_cancelled,
        'gym_total': gym_total,
        'gym_pending': gym_pending,
        'gym_uploaded': gym_uploaded,
        'gym_confirmed': gym_confirmed,
        'gym_cancelled': gym_cancelled,
        'service_total': service_total,
        'service_pending': service_pending,
        'service_uploaded': service_uploaded,
        'service_confirmed': service_confirmed,
        'service_cancelled': service_cancelled,
        'service_income': service_income,
        'pending_service_payments': pending_service_payments,
        'all_service_reservations': all_service_reservations,
        'svc_status_filter': svc_status_filter,
        'svc_cat_filter': svc_cat_filter,
        'svc_status_choices': ServiceReservation.STATUS_CHOICES,
        'svc_cat_choices': ServiceReservation.CATEGORY_CHOICES,
        # Eventos
        'event_inquiries': event_inquiries,
        'total_event_inquiries': total_event_inquiries,
        'unread_events': unread_events,
        'event_type_choices': EventInquiry.EVENT_TYPE_CHOICES,
        'salon_choices': EventInquiry.SALON_CHOICES,
        'is_readonly': _is_recepcionista(request.user),
    }
    return render(request, 'staff/dashboard.html', context)


@staff_required
def reservation_detail(request, reservation_id):
    """Detalle completo de una reservación"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    payments = reservation.payments.all().order_by('-payment_date')

    can_delete = request.user.is_superuser or request.user.groups.filter(name='Super Administradores').exists()
    context = {
        'reservation': reservation,
        'payments': payments,
        'is_readonly': _is_recepcionista(request.user),
        'can_delete': can_delete,
    }
    return render(request, 'staff/reservation_details.html', context)


@staff_required
def service_reservation_detail(request, reservation_id):
    """Detalle completo de una reservación de servicio Spa/Gym"""
    reservation = get_object_or_404(ServiceReservation, id=reservation_id)
    payments = reservation.payments.all().order_by('-payment_date')

    can_delete = request.user.is_superuser or request.user.groups.filter(name='Super Administradores').exists()
    context = {
        'reservation': reservation,
        'payments': payments,
        'is_readonly': _is_recepcionista(request.user),
        'is_service': True,
        'can_delete': can_delete,
    }
    return render(request, 'staff/reservation_details.html', context)


def _send_service_email(request, reservation, payment, action, notes=''):
    """Enviar correo de confirmación/rechazo para servicios Spa/Gym"""
    customer_email = reservation.customer.user.email
    if not customer_email:
        return

    portal_url = request.build_absolute_uri('/')

    if action == 'verify':
        context = {
            'customer_name': reservation.customer.user.first_name,
            'reservation_id': reservation.id,
            'service_name': reservation.service_name,
            'service_category': reservation.get_service_category_display(),
            'preferred_date': reservation.preferred_date.strftime('%d/%m/%Y'),
            'portal_url': portal_url,
            'year': date.today().year,
        }
        html_message = render_to_string('staff/emails/spa_gym_verified.html', context)
        subject = f'Confirmación de Reserva - {reservation.get_service_category_display()}'
        text_content = f'Hola {reservation.customer.user.first_name},\n\nTu pago ha sido verificado y tu reserva de {reservation.get_service_category_display()} está confirmada.\n\n¡Gracias por elegir D\'Spa Hotel!'
    else:
        context = {
            'customer_name': reservation.customer.user.first_name,
            'reservation_id': reservation.id,
            'notes': notes,
            'portal_url': portal_url,
            'year': date.today().year,
        }
        html_message = render_to_string('staff/emails/spa_gym_rejected.html', context)
        subject = 'Problema con tu Pago de Servicio'
        text_content = f'Hola {reservation.customer.user.first_name},\n\nHemos detectado un problema con tu comprobante de pago. Por favor, sube un nuevo comprobante.'

    from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@dspahotel.com'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [customer_email])
    msg.attach_alternative(html_message, "text/html")

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo', 'logo de empresa.PNG')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as img:
            logo_image = MIMEImage(img.read())
            logo_image.add_header('Content-ID', '<logo>')
            msg.attach(logo_image)

    msg.send(fail_silently=False)


@can_edit_services_required
def verify_service_payment(request, payment_id):
    """Verificar o rechazar un comprobante de pago de servicio"""
    payment = get_object_or_404(ServicePaymentProof, id=payment_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('staff_notes', '')
        payment.staff_notes = notes

        if action == 'verify':
            payment.verification_status = 'verified'
            payment.save()
            payment.service_reservation.status = 'confirmed'
            payment.service_reservation.save()
            messages.success(request, f'Pago verificado. Reserva de servicio #{payment.service_reservation.id} confirmada.')
            log_audit(request, 'service_verify', f'Pago de servicio #{payment.id} verificado. Reserva #{payment.service_reservation.id} confirmada.')
            _send_service_email(request, payment.service_reservation, payment, 'verify')

        elif action == 'reject':
            payment.verification_status = 'rejected'
            payment.save()
            payment.service_reservation.status = 'pending'
            payment.service_reservation.save()
            messages.warning(request, f'Pago rechazado para Reserva de servicio #{payment.service_reservation.id}.')
            log_audit(request, 'service_reject', f'Pago de servicio #{payment.id} rechazado. Reserva #{payment.service_reservation.id}.')
            _send_service_email(request, payment.service_reservation, payment, 'reject', notes)

        return redirect('staff_service_detail', reservation_id=payment.service_reservation.id)

    context = {
        'payment': payment,
        'reservation': payment.service_reservation,
        'is_service': True,
    }
    return render(request, 'staff/verify_payment.html', context)


@can_edit_services_required
def update_service_status(request, reservation_id):
    """Actualizar estado de una reservación de servicio"""
    reservation = get_object_or_404(ServiceReservation, id=reservation_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(ServiceReservation.STATUS_CHOICES):
            old_status = reservation.status
            reservation.status = new_status
            reservation.save()

            status_labels = dict(ServiceReservation.STATUS_CHOICES)
            messages.success(
                request,
                f'Servicio #{reservation.id} actualizado de "{status_labels.get(old_status, old_status)}" a "{status_labels.get(new_status, new_status)}".'
            )
            log_audit(request, 'service_status', f'Servicio #{reservation.id} actualizado de "{status_labels.get(old_status, old_status)}" a "{status_labels.get(new_status, new_status)}".')

    return redirect('staff_service_detail', reservation_id=reservation.id)


@superuser_required
def delete_service_reservation(request, reservation_id):
    """Eliminar una reservación de servicio Spa/Gym (solo superusuario)"""
    reservation = get_object_or_404(ServiceReservation, id=reservation_id)

    if request.method == 'POST':
        res_id = reservation.id
        category_name = reservation.get_service_category_display()
        reservation.delete()
        messages.success(request, f'Reservación de {category_name} #{res_id} eliminada exitosamente del sistema.')
        log_audit(request, 'service_delete', f'Reservación de {category_name} #{res_id} eliminada del sistema.')
        return redirect(f"{reverse('staff_dashboard')}?mode=spa_gym")

    return redirect('staff_service_detail', reservation_id=reservation.id)


@staff_required
def mark_event_read(request, inquiry_id):
    """Marcar una consulta de evento como leída o respondida"""
    inquiry = get_object_or_404(EventInquiry, id=inquiry_id)
    if request.method == 'POST':
        action = request.POST.get('action', 'read')
        if action == 'respond':
            inquiry.is_responded = True
            inquiry.is_read = True
            messages.success(request, f'Consulta #{inquiry.id} de {inquiry.name} marcada como respondida.')
        elif action == 'unread':
            inquiry.is_read = False
            inquiry.is_responded = False
            messages.info(request, f'Consulta #{inquiry.id} marcada como no leída.')
        else:
            inquiry.is_read = True
            messages.success(request, f'Consulta #{inquiry.id} de {inquiry.name} marcada como leída.')
        inquiry.save()
        log_audit(request, 'event_read', f'Consulta de evento #{inquiry.id} de "{inquiry.name}" marcada como {action}.')
    return redirect('staff_dashboard')


@staff_required
def create_event_inquiry_staff(request):
    """Permitir al personal registrar una consulta de salón presencial o telefónica"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        event_type = request.POST.get('event_type', '')
        salon_preference = request.POST.get('salon_preference', '')
        estimated_guests = request.POST.get('estimated_guests', 1)
        preferred_date = request.POST.get('preferred_date', '')
        message = request.POST.get('message', '').strip()

        if name and event_type and salon_preference and preferred_date:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(preferred_date, '%Y-%m-%d').date()
            except ValueError:
                date_obj = None

            if date_obj:
                inquiry = EventInquiry.objects.create(
                    name=name,
                    email=email or 'N/A',
                    phone=phone or 'N/A',
                    event_type=event_type,
                    salon_preference=salon_preference,
                    estimated_guests=int(estimated_guests or 1),
                    preferred_date=date_obj,
                    message=message or 'Consulta registrada directamente por recepción.',
                    is_read=True,
                )
                messages.success(request, f'Consulta de salón #{inquiry.id} para "{inquiry.name}" registrada exitosamente.')
                log_audit(request, 'event_created', f'Consulta de salón #{inquiry.id} para "{inquiry.name}" registrada por personal.')
            else:
                messages.error(request, 'La fecha del evento no es válida.')
        else:
            messages.error(request, 'Por favor complete todos los campos obligatorios.')

    return redirect('staff_dashboard')


@can_edit_required
def delete_event_inquiry(request, inquiry_id):
    """Eliminar consulta de salón"""
    inquiry = get_object_or_404(EventInquiry, id=inquiry_id)
    if request.method == 'POST':
        inquiry_name = inquiry.name
        inquiry.delete()
        messages.success(request, f'Consulta #{inquiry_id} eliminada.')
        log_audit(request, 'event_deleted', f'Consulta de evento #{inquiry_id} de "{inquiry_name}" eliminada.')
    return redirect('staff_dashboard')


@can_edit_required
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
            log_audit(request, 'verify_payment', f'Pago #{payment.id} verificado. Reservación #{payment.reservation.id} confirmada.')
            
            # Enviar correo de confirmación
            customer_email = payment.reservation.customer.user.email
            if customer_email:
                logo_url = request.build_absolute_uri(static('images/logo/logo de empresa.PNG'))
                portal_url = request.build_absolute_uri('/')
                
                context = {
                    'customer_name': payment.reservation.customer.user.first_name,
                    'reservation_id': payment.reservation.id,
                    'service_name': payment.reservation.get_service_type_display(),
                    'check_in': payment.reservation.check_in.strftime('%d/%m/%Y'),
                    'check_out': payment.reservation.check_out.strftime('%d/%m/%Y'),
                    'portal_url': portal_url,
                    'year': date.today().year,
                }
                html_message = render_to_string('staff/emails/payment_verified.html', context)
                
                subject = 'Confirmación de Pago y Reservación'
                text_content = f'Hola {payment.reservation.customer.user.first_name},\n\nTu pago ha sido verificado y tu reservación está confirmada.\n\n¡Gracias por elegir DSPA Hotel!'
                from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@dspahotel.com'
                
                msg = EmailMultiAlternatives(subject, text_content, from_email, [customer_email])
                msg.attach_alternative(html_message, "text/html")
                
                logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo', 'logo de empresa.PNG')
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as img:
                        logo_image = MIMEImage(img.read())
                        logo_image.add_header('Content-ID', '<logo>')
                        msg.attach(logo_image)
                        
                msg.send(fail_silently=False)

        elif action == 'reject':
            payment.verification_status = 'rejected'
            payment.save()
            payment.reservation.status = 'pending'
            payment.reservation.save()
            messages.warning(request, f'Pago rechazado para Reservación #{payment.reservation.id}.')
            log_audit(request, 'reject_payment', f'Pago #{payment.id} rechazado. Reservación #{payment.reservation.id}.')
            
            # Enviar correo de rechazo
            customer_email = payment.reservation.customer.user.email
            if customer_email:
                logo_url = request.build_absolute_uri(static('images/logo/logo de empresa.PNG'))
                portal_url = request.build_absolute_uri('/')
                
                context = {
                    'customer_name': payment.reservation.customer.user.first_name,
                    'reservation_id': payment.reservation.id,
                    'notes': notes,
                    'portal_url': portal_url,
                    'year': date.today().year,
                }
                html_message = render_to_string('staff/emails/payment_rejected.html', context)
                
                reason = f"Notas del personal: {notes}\n" if notes else ""
                subject = 'Problema con tu Pago de Reservación'
                text_content = f'Hola {payment.reservation.customer.user.first_name},\n\nHemos detectado un problema al verificar el pago de su reservación. El comprobante subido ha sido rechazado.\n\n{reason}Por favor, contacta con nosotros para más información o sube un nuevo comprobante.\n\nAtentamente,\nEl equipo de DSPA Hotel.'
                from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@dspahotel.com'
                
                msg = EmailMultiAlternatives(subject, text_content, from_email, [customer_email])
                msg.attach_alternative(html_message, "text/html")
                
                logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo', 'logo de empresa.PNG')
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as img:
                        logo_image = MIMEImage(img.read())
                        logo_image.add_header('Content-ID', '<logo>')
                        msg.attach(logo_image)
                        
                msg.send(fail_silently=False)

        return redirect('staff_reservation_detail', reservation_id=payment.reservation.id)

    context = {
        'payment': payment,
        'reservation': payment.reservation,
    }
    return render(request, 'staff/verify_payment.html', context)


@can_edit_required
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

            status_labels = dict(Reservation.STATUS_CHOICES)
            messages.success(
                request,
                f'Reservación #{reservation.id} actualizada de "{status_labels.get(old_status, old_status)}" a "{status_labels.get(new_status, new_status)}".'
            )
            log_audit(request, 'update_status', f'Reservación #{reservation.id} actualizada de "{status_labels.get(old_status, old_status)}" a "{status_labels.get(new_status, new_status)}".')

    return redirect('staff_reservation_detail', reservation_id=reservation.id)


@superuser_required
def delete_reservation(request, reservation_id):
    """Eliminar una reservación del sistema (solo superusuario)"""
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == 'POST':
        res_id = reservation.id
        # Liberar habitación si tenía una asignada
        if reservation.room:
            reservation.room.status = 'available'
            reservation.room.save()
        reservation.delete()
        messages.success(request, f'Reservación #{res_id} eliminada exitosamente del sistema.')
        log_audit(request, 'delete_reservation', f'Reservación #{res_id} eliminada del sistema.')
        return redirect('staff_dashboard')

    return redirect('staff_reservation_detail', reservation_id=reservation.id)

@staff_required
def room_management(request):
    """Gestión de habitaciones"""
    rooms = Room.objects.all().order_by('floor', 'room_number')
    readonly = _is_recepcionista(request.user)

    # Filtros
    floor_filter = request.GET.get('floor', '')
    channel_filter = request.GET.get('channel', '')
    type_filter = request.GET.get('type', '')

    if floor_filter:
        rooms = rooms.filter(floor=int(floor_filter))
    if channel_filter:
        rooms = rooms.filter(sales_channel=channel_filter)
    if type_filter:
        rooms = rooms.filter(room_type=type_filter)

    if request.method == 'POST' and not readonly:
        room_id = request.POST.get('room_id')
        new_status = request.POST.get('status')
        new_channel = request.POST.get('sales_channel')
        room = get_object_or_404(Room, id=room_id)

        if new_status:
            room.status = new_status
        if new_channel:
            room.sales_channel = new_channel

        room.save()
        messages.success(request, f'Habitación {room.room_number} actualizada.')
        log_audit(request, 'room_update', f'Habitación {room.room_number} actualizada. Estado: {room.status}, Canal: {room.sales_channel}.')
    elif request.method == 'POST' and readonly:
        messages.error(request, 'No tienes permisos para modificar habitaciones.')

    # Pisos disponibles para el filtro
    floors = sorted(set(Room.objects.values_list('floor', flat=True)))

    context = {
        'rooms': rooms,
        'is_readonly': readonly,
        'floors': floors,
        'floor_filter': floor_filter,
        'channel_filter': channel_filter,
        'type_filter': type_filter,
    }
    return render(request, 'staff/room_management.html', context)


# ============================================================
# GESTION DE USUARIOS DE ADMINISTRACION
# Solo accesible por el superusuario
# ============================================================

ROLE_CHOICES = [
    ('super_admin', 'Super Administrador'),
    ('encargado_reservas', 'Encargado de Reservaciones'),
    ('recepcionista', 'Recepcionista de Datos'),
    ('operador_aqua', 'Operador Aqua Spa Gym'),
]

ROLE_DESCRIPTIONS = {
    'super_admin': 'Acceso total al sistema. Puede crear, editar, eliminar y gestionar usuarios.',
    'encargado_reservas': 'Puede ver, crear y editar reservaciones y planillas. No puede eliminar ni gestionar usuarios.',
    'recepcionista': 'Solo lectura. Puede ver información pero no crear, editar ni eliminar nada.',
    'operador_aqua': 'Gestiona solo las reservaciones de Spa y Gimnasio. No tiene acceso a habitaciones ni gestión de usuarios.',
}

ROLE_TO_GROUP = {
    'super_admin': 'Super Administradores',
    'encargado_reservas': 'Encargados de Reservaciones',
    'recepcionista': 'Recepcionistas de Datos',
    'operador_aqua': 'Operadores Aqua Spa Gym',
}


def _get_user_role(user):
    """Obtener el rol de un usuario basado en sus grupos"""
    if user.is_superuser:
        return 'super_admin'
    if user.groups.filter(name='Encargados de Reservaciones').exists():
        return 'encargado_reservas'
    if user.groups.filter(name='Operadores Aqua Spa Gym').exists():
        return 'operador_aqua'
    if user.groups.filter(name='Recepcionistas de Datos').exists():
        return 'recepcionista'
    return 'sin_rol'


def _get_user_role_display(user):
    """Obtener el nombre visible del rol"""
    role = _get_user_role(user)
    role_dict = dict(ROLE_CHOICES)
    return role_dict.get(role, 'Sin Rol')


@superuser_required
def user_management(request):
    """Vista principal: lista todos los usuarios staff"""
    staff_users = User.objects.filter(is_staff=True).order_by('-is_superuser', 'username')

    users_with_roles = []
    for user in staff_users:
        users_with_roles.append({
            'user': user,
            'role': _get_user_role(user),
            'role_display': _get_user_role_display(user),
        })

    context = {
        'users_with_roles': users_with_roles,
        'role_choices': ROLE_CHOICES,
        'role_descriptions': ROLE_DESCRIPTIONS,
    }
    return render(request, 'staff/user_management.html', context)


@superuser_required
def create_user(request):
    """Crear un nuevo usuario de administración"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '')

        # Validaciones
        errors = []
        if not username:
            errors.append('El nombre de usuario es obligatorio.')
        if not password:
            errors.append('La contraseña es obligatoria.')
        if len(password) < 6:
            errors.append('La contraseña debe tener al menos 6 caracteres.')
        if not role or role not in dict(ROLE_CHOICES):
            errors.append('Debe seleccionar un rol válido.')
        if User.objects.filter(username=username).exists():
            errors.append(f'El usuario "{username}" ya existe.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('user_management')

        # Crear usuario
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        user.is_staff = True

        if role == 'super_admin':
            user.is_superuser = True

        user.save()

        # Asignar grupo
        group_name = ROLE_TO_GROUP.get(role)
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.clear()
            user.groups.add(group)

        messages.success(
            request,
            f'Usuario "{username}" creado exitosamente con rol "{dict(ROLE_CHOICES)[role]}".'
        )
        log_audit(request, 'create_user', f'Usuario "{username}" creado con rol "{dict(ROLE_CHOICES)[role]}".')
        return redirect('user_management')

    return redirect('user_management')


@superuser_required
def edit_user(request, user_id):
    """Editar un usuario existente"""
    target_user = get_object_or_404(User, id=user_id, is_staff=True)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '')
        new_password = request.POST.get('new_password', '').strip()

        # No permitir que el superusuario se cambie su propio rol
        if target_user == request.user and role != 'super_admin':
            messages.error(request, 'No puedes cambiar tu propio rol de Super Administrador.')
            return redirect('user_management')

        # Actualizar datos
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.email = email

        if role:
            # Actualizar superuser status
            target_user.is_superuser = (role == 'super_admin')

            # Actualizar grupo
            group_name = ROLE_TO_GROUP.get(role)
            if group_name:
                group, _ = Group.objects.get_or_create(name=group_name)
                target_user.groups.clear()
                target_user.groups.add(group)

        if new_password and len(new_password) >= 6:
            target_user.set_password(new_password)

        target_user.save()
        messages.success(request, f'Usuario "{target_user.username}" actualizado exitosamente.')
        log_audit(request, 'edit_user', f'Usuario "{target_user.username}" editado.')
        return redirect('user_management')

    # GET: mostrar formulario con datos actuales
    context = {
        'target_user': target_user,
        'current_role': _get_user_role(target_user),
        'role_choices': ROLE_CHOICES,
        'role_descriptions': ROLE_DESCRIPTIONS,
    }
    return render(request, 'staff/edit_user.html', context)


@superuser_required
def delete_user(request, user_id):
    """Eliminar un usuario staff"""
    target_user = get_object_or_404(User, id=user_id, is_staff=True)

    if target_user == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('user_management')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f'Usuario "{username}" eliminado exitosamente.')
        log_audit(request, 'delete_user', f'Usuario "{username}" eliminado del sistema.')

    return redirect('user_management')


# ============================================================
# HISTORIAL DE AUDITORÍA
# Solo accesible por el superusuario
# ============================================================

@superuser_required
def audit_log_view(request):
    """Vista del historial de auditoría"""
    logs = AuditLog.objects.select_related('user').all()

    # Filtros
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if action_filter:
        logs = logs.filter(action=action_filter)
    if user_filter:
        logs = logs.filter(user__id=user_filter)
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    logs = logs[:300]
    staff_users = User.objects.filter(is_staff=True).order_by('username')

    context = {
        'logs': logs,
        'action_choices': AuditLog.ACTION_CHOICES,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'staff_users': staff_users,
    }
    return render(request, 'staff/audit_log.html', context)


# ============================================================
# RESPALDO Y RESTAURACIÓN DE BASE DE DATOS
# Solo accesible por el superusuario
# ============================================================

@superuser_required
def backup_database(request):
    """Vista principal de respaldos y crear nuevo respaldo"""
    backup_dir = Path(settings.BASE_DIR) / 'backups'

    if request.method == 'POST':
        backup_dir.mkdir(exist_ok=True)
        db_path = settings.DATABASES['default']['NAME']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'db_backup_{timestamp}.sqlite3'
        backup_path = backup_dir / backup_name

        try:
            if Path(str(db_path)).exists():
                shutil.copy2(str(db_path), str(backup_path))
            else:
                # Fallback para bases de datos SQLite en memoria
                import sqlite3
                conn = sqlite3.connect(str(backup_path))
                conn.execute("CREATE TABLE IF NOT EXISTS _backup_meta (created_at TIMESTAMP)")
                conn.close()

            log_audit(request, 'backup_created', f'Respaldo de base de datos creado: {backup_name}')
            messages.success(request, f'Respaldo creado exitosamente: {backup_name}')
        except Exception as e:
            messages.error(request, f'Error al crear el respaldo: {str(e)}')

        return redirect('backup_restore')

    # Listar respaldos existentes
    backups = []
    if backup_dir.exists():
        for f in sorted(backup_dir.glob('db_backup_*.sqlite3'), reverse=True):
            size_mb = f.stat().st_size / (1024 * 1024)
            try:
                file_date = datetime.strptime(f.stem.replace('db_backup_', ''), '%Y%m%d_%H%M%S')
            except ValueError:
                file_date = datetime.fromtimestamp(f.stat().st_mtime)
            backups.append({
                'name': f.name,
                'size': f'{size_mb:.2f} MB',
                'date': file_date,
            })

    # También listar los respaldos de seguridad (pre-restore)
    safety_backups = []
    if backup_dir.exists():
        for f in sorted(backup_dir.glob('db_pre_restore_*.sqlite3'), reverse=True):
            size_mb = f.stat().st_size / (1024 * 1024)
            safety_backups.append({
                'name': f.name,
                'size': f'{size_mb:.2f} MB',
                'date': datetime.fromtimestamp(f.stat().st_mtime),
            })

    context = {
        'backups': backups,
        'safety_backups': safety_backups,
    }
    return render(request, 'staff/backup_restore.html', context)


@superuser_required
def download_backup(request, filename):
    """Descargar un archivo de respaldo"""
    backup_dir = Path(settings.BASE_DIR) / 'backups'
    file_path = backup_dir / filename

    if not file_path.exists() or not (filename.startswith('db_backup_') or filename.startswith('db_pre_restore_')):
        messages.error(request, 'El archivo de respaldo no existe.')
        return redirect('backup_restore')

    return FileResponse(open(str(file_path), 'rb'), as_attachment=True, filename=filename)


@superuser_required
def delete_backup(request, filename):
    """Eliminar un archivo de respaldo"""
    if request.method == 'POST':
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        file_path = backup_dir / filename

        if file_path.exists() and (filename.startswith('db_backup_') or filename.startswith('db_pre_restore_')):
            file_path.unlink()
            log_audit(request, 'backup_deleted', f'Respaldo eliminado: {filename}')
            messages.success(request, f'Respaldo "{filename}" eliminado exitosamente.')
        else:
            messages.error(request, 'Archivo de respaldo no encontrado.')

    return redirect('backup_restore')


@superuser_required
def restore_database(request):
    """Restaurar la base de datos desde un respaldo"""
    if request.method == 'POST':
        filename = request.POST.get('filename', '')
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_path = backup_dir / filename
        db_path = Path(str(settings.DATABASES['default']['NAME']))

        if not backup_path.exists() or not (filename.startswith('db_backup_') or filename.startswith('db_pre_restore_')):
            messages.error(request, 'El archivo de respaldo no existe.')
            return redirect('backup_restore')

        try:
            # Crear respaldo de seguridad antes de restaurar
            backup_dir.mkdir(exist_ok=True)
            safety_name = f'db_pre_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sqlite3'
            safety_path = backup_dir / safety_name
            if db_path.exists():
                shutil.copy2(str(db_path), str(safety_path))

            # Cerrar conexiones activas
            from django.db import connections
            for conn in connections.all():
                conn.close()

            # Restaurar
            if db_path.exists():
                shutil.copy2(str(backup_path), str(db_path))

            log_audit(request, 'backup_restored', f'Base de datos restaurada desde: {filename}')

            messages.success(
                request,
                f'Base de datos restaurada exitosamente desde "{filename}". '
                f'Se creó un respaldo de seguridad automático: "{safety_name}".'
            )
        except Exception as e:
            messages.error(request, f'Error al restaurar la base de datos: {str(e)}')

        return redirect('backup_restore')

    return redirect('backup_restore')


# ============================================================
# MANUAL DE USO DEL SISTEMA
# Accesible para todo el staff, contenido según rol
# ============================================================

@staff_required
def user_manual(request):
    """Manual de uso del sistema - contenido filtrado por rol"""
    user_role = _get_user_role(request.user)
    role_display = _get_user_role_display(request.user)

    context = {
        'user_role': user_role,
        'role_display': role_display,
        'is_super_admin': request.user.is_superuser,
        'is_encargado': user_role == 'encargado_reservas',
        'is_recepcionista': user_role == 'recepcionista',
        'is_operador_aqua': user_role == 'operador_aqua',
    }
    return render(request, 'staff/user_manual.html', context)
