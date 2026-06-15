from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Service, Room, RoomImage, ContactInfo, HotelInfo
from datetime import datetime, timedelta


def home(request):
    hotel_info = HotelInfo.objects.first()
    # Get one of each type
    featured_rooms = []
    matrimonial = Room.objects.filter(room_type='matrimonial', is_active=True).first()
    double = Room.objects.filter(room_type='double', is_active=True).first()
    if matrimonial: featured_rooms.append(matrimonial)
    if double: featured_rooms.append(double)
    
    services = Service.objects.filter(is_active=True).order_by('order')[:6]

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    context = {
        'hotel_info': hotel_info,
        'featured_rooms': featured_rooms,
        'services': services,
        'today': today.strftime('%Y-%m-%d'),
        'tomorrow': tomorrow.strftime('%Y-%m-%d'),
    }
    return render(request, 'core/home.html', context)


def search_availability(request):
    """API para buscar habitaciones disponibles en tiempo real"""
    if request.method == 'GET':
        check_in = request.GET.get('check_in')
        check_out = request.GET.get('check_out')
        adults = int(request.GET.get('adults', 1))
        children = int(request.GET.get('children', 0))

        if check_in and check_out:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

            from reservations.models import Reservation
            occupied_rooms = Reservation.objects.filter(
                room__isnull=False,
                status__in=['confirmed', 'payment_uploaded'],
                check_in__lt=check_out_date,
                check_out__gt=check_in_date
            ).values_list('room_id', flat=True)

            available_matrimonial = Room.objects.filter(
                room_type='matrimonial', is_active=True
            ).exclude(id__in=occupied_rooms)

            available_double = Room.objects.filter(
                room_type='double', is_active=True
            ).exclude(id__in=occupied_rooms)

            total_guests = adults + children
            available_matrimonial = [room for room in available_matrimonial if room.capacity_adults + room.capacity_children >= total_guests]
            available_double = [room for room in available_double if room.capacity_adults + room.capacity_children >= total_guests]

            nights = (check_out_date - check_in_date).days
            
            mat_room = available_matrimonial[0] if available_matrimonial else None
            dob_room = available_double[0] if available_double else None

            return JsonResponse({
                'success': True,
                'nights': nights,
                'matrimonial_count': len(available_matrimonial),
                'double_count': len(available_double),
                'matrimonial_room': {
                    'id': mat_room.id,
                    'number': mat_room.room_number,
                    'price': str(mat_room.price_per_night),
                    'total': str(mat_room.price_per_night * nights),
                    'description': mat_room.description,
                    'capacity_adults': mat_room.capacity_adults,
                    'capacity_children': mat_room.capacity_children,
                } if mat_room else None,
                'double_room': {
                    'id': dob_room.id,
                    'number': dob_room.room_number,
                    'price': str(dob_room.price_per_night),
                    'total': str(dob_room.price_per_night * nights),
                    'description': dob_room.description,
                    'capacity_adults': dob_room.capacity_adults,
                    'capacity_children': dob_room.capacity_children,
                } if dob_room else None,
            })

    return JsonResponse({'success': False})


def about(request):
    hotel_info = HotelInfo.objects.first()
    context = {'hotel_info': hotel_info}
    return render(request, 'core/about.html', context)


def services_view(request):
    services = Service.objects.filter(is_active=True).order_by('category', 'order')
    wellness_services = services.filter(category='wellness')
    corporate_services = services.filter(category='corporate')
    general_services = services.filter(category='general')

    context = {
        'wellness_services': wellness_services,
        'corporate_services': corporate_services,
        'general_services': general_services,
    }
    return render(request, 'core/services.html', context)


def rooms_view(request):
    matrimonial_rooms = Room.objects.filter(room_type='matrimonial', is_active=True)
    double_rooms = Room.objects.filter(room_type='double', is_active=True)

    context = {
        'matrimonial_rooms': matrimonial_rooms,
        'double_rooms': double_rooms,
    }
    return render(request, 'core/rooms.html', context)


def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id, is_active=True)
    context = {
        'room': room,
    }
    return render(request, 'core/room_detail.html', context)


def contact(request):
    contact_info = ContactInfo.objects.first()
    context = {'contact_info': contact_info}
    return render(request, 'core/contact.html', context)


def location(request):
    contact_info = ContactInfo.objects.first()
    context = {'contact_info': contact_info}
    return render(request, 'core/location.html', context)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            login(request, user)
            messages.success(request, 'Registro exitoso. Complete sus datos para continuar.')
            return redirect('complete_profile')
        else:
            messages.error(request, 'Por favor corrija los errores del formulario.')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})


@login_required
def complete_profile(request):
    from reservations.models import Customer
    try:
        customer = Customer.objects.get(user=request.user)
        if request.method != 'POST':
            return redirect('home')
    except Customer.DoesNotExist:
        customer = None

    if request.method == 'POST':
        if customer:
            customer.phone = request.POST.get('phone', customer.phone)
            customer.address = request.POST.get('address', customer.address)
            customer.save()
        else:
            Customer.objects.create(
                user=request.user,
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                id_document=request.POST.get('id_document', ''),
                birth_date=request.POST.get('birth_date', '2000-01-01'),
            )
        messages.success(request, 'Perfil completado exitosamente.')
        return redirect('home')
    return render(request, 'core/complete_profile.html')
