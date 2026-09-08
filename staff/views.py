from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from reservations.models import Reservation, PaymentProof, Customer
from core.models import Room
from .models import StaffProfile
from datetime import datetime, date
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.templatetags.static import static
from email.mime.image import MIMEImage
import os

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
    """Decorador: solo superusuarios pueden acceder"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, 'Solo el administrador principal puede gestionar usuarios.')
            return redirect('staff_dashboard')
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
        'is_readonly': _is_recepcionista(request.user),
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
        'is_readonly': _is_recepcionista(request.user),
    }
    return render(request, 'staff/reservation_details.html', context)


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
                text_content = f'Hola {payment.reservation.customer.user.first_name},\n\nLamentablemente, ha habido un problema al verificar el pago de tu reservación. El comprobante ha sido rechazado.\n\n{reason}Por favor, contacta con nosotros para más información o sube un nuevo comprobante.\n\nAtentamente,\nEl equipo de DSPA Hotel.'
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
]

ROLE_DESCRIPTIONS = {
    'super_admin': 'Acceso total al sistema. Puede crear, editar, eliminar y gestionar usuarios.',
    'encargado_reservas': 'Puede ver, crear y editar reservaciones y planillas. No puede eliminar ni gestionar usuarios.',
    'recepcionista': 'Solo lectura. Puede ver información pero no crear, editar ni eliminar nada.',
}

ROLE_TO_GROUP = {
    'super_admin': 'Super Administradores',
    'encargado_reservas': 'Encargados de Reservaciones',
    'recepcionista': 'Recepcionistas de Datos',
}


def _get_user_role(user):
    """Obtener el rol de un usuario basado en sus grupos"""
    if user.is_superuser:
        return 'super_admin'
    if user.groups.filter(name='Encargados de Reservaciones').exists():
        return 'encargado_reservas'
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

        # Validar rol
        if role and role not in dict(ROLE_CHOICES):
            messages.error(request, 'Rol inválido.')
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

    return redirect('user_management')

