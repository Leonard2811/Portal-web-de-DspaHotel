from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from google import genai
from google.genai import types
from .models import Service, Room, RoomImage, ContactInfo, HotelInfo
from datetime import datetime, timedelta


def home(request):
    hotel_info = HotelInfo.objects.first()
    # Get one of each type
    featured_rooms = []
    deluxe = Room.objects.filter(room_type='deluxe', is_active=True, sales_channel='web').first()
    doble = Room.objects.filter(room_type='doble', is_active=True, sales_channel='web').first()
    if deluxe: featured_rooms.append(deluxe)
    if doble: featured_rooms.append(doble)
    
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

            available_deluxe = Room.objects.filter(
                room_type='deluxe', is_active=True, sales_channel='web'
            ).exclude(id__in=occupied_rooms)

            available_doble = Room.objects.filter(
                room_type='doble', is_active=True, sales_channel='web'
            ).exclude(id__in=occupied_rooms)

            total_guests = adults + children
            available_deluxe = [room for room in available_deluxe if room.capacity_adults + room.capacity_children >= total_guests]
            available_doble = [room for room in available_doble if room.capacity_adults + room.capacity_children >= total_guests]

            nights = (check_out_date - check_in_date).days
            
            deluxe_room = available_deluxe[0] if available_deluxe else None
            doble_room = available_doble[0] if available_doble else None

            return JsonResponse({
                'success': True,
                'nights': nights,
                'deluxe_count': len(available_deluxe),
                'doble_count': len(available_doble),
                'deluxe_room': {
                    'id': deluxe_room.id,
                    'number': deluxe_room.room_number,
                    'price': str(deluxe_room.price_per_night),
                    'total': str(deluxe_room.price_per_night * nights),
                    'description': deluxe_room.description,
                    'capacity_adults': deluxe_room.capacity_adults,
                    'capacity_children': deluxe_room.capacity_children,
                    'extra_guest_fee': str(deluxe_room.extra_guest_fee),
                } if deluxe_room else None,
                'doble_room': {
                    'id': doble_room.id,
                    'number': doble_room.room_number,
                    'price': str(doble_room.price_per_night),
                    'total': str(doble_room.price_per_night * nights),
                    'description': doble_room.description,
                    'capacity_adults': doble_room.capacity_adults,
                    'capacity_children': doble_room.capacity_children,
                    'extra_guest_fee': str(doble_room.extra_guest_fee),
                } if doble_room else None,
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
    deluxe_rooms = Room.objects.filter(room_type='deluxe', is_active=True, sales_channel='web')
    doble_rooms = Room.objects.filter(room_type='doble', is_active=True, sales_channel='web')

    context = {
        'deluxe_rooms': deluxe_rooms,
        'doble_rooms': doble_rooms,
    }
    return render(request, 'core/rooms.html', context)


def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id, is_active=True, sales_channel='web')
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


def check_hotel_availability(check_in_date: str, check_out_date: str, adults: int = 1) -> str:
    """Busca disponibilidad de habitaciones en el hotel D'Spa para las fechas dadas.
    Args:
        check_in_date: Fecha de entrada en formato YYYY-MM-DD.
        check_out_date: Fecha de salida en formato YYYY-MM-DD.
        adults: Número de huéspedes adultos (opcional, por defecto 1).
    """
    try:
        from reservations.models import Reservation
        from core.models import Room
        from datetime import datetime
        ci = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        co = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        
        if co <= ci:
            return "Error: La fecha de salida debe ser posterior a la fecha de entrada."
            
        occupied_rooms = Reservation.objects.filter(
            room__isnull=False,
            status__in=['confirmed', 'payment_uploaded'],
            check_in__lt=co,
            check_out__gt=ci
        ).values_list('room_id', flat=True)

        available_deluxe = Room.objects.filter(
            room_type='deluxe', is_active=True, sales_channel='web'
        ).exclude(id__in=occupied_rooms)

        available_doble = Room.objects.filter(
            room_type='doble', is_active=True, sales_channel='web'
        ).exclude(id__in=occupied_rooms)

        available_deluxe = [r for r in available_deluxe if r.capacity_adults + r.capacity_children >= adults]
        available_doble = [r for r in available_doble if r.capacity_adults + r.capacity_children >= adults]
        
        return f"Disponibilidad para {adults} huéspedes del {check_in_date} al {check_out_date}: {len(available_deluxe)} habitaciones Deluxe disponibles, {len(available_doble)} habitaciones Dobles disponibles."
    except Exception as e:
        return f"Error al buscar disponibilidad: {str(e)}. Pide al usuario que intente con un formato YYYY-MM-DD."


@csrf_exempt
def chatbot_api(request):
    """API para el chatbot potenciado por IA (Gemini)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Solo se permiten peticiones POST'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        history = data.get('history', [])

        if not user_message:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)

        from dotenv import dotenv_values
        from django.conf import settings
        env_path = os.path.join(settings.BASE_DIR, '.env')
        env_vars = dotenv_values(env_path)
        api_key = env_vars.get('GEMINI_API_KEY', '').strip()
        
        if not api_key:
            return JsonResponse({'reply': 'La IA no está configurada (Falta API Key). Contacte al administrador.'})

        client = genai.Client(api_key=api_key)
        
        # Format history for Gemini
        gemini_history = []
        for msg in history:
            role = 'user' if msg.get('role') == 'user' else 'model'
            gemini_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.get('text', ''))]))
            
        # System prompt with hotel details and instructions
        today_str = datetime.now().strftime('%Y-%m-%d')
        system_instruction = f"""
        Eres el asistente virtual oficial de D'Spa Hotel. Tu tarea es responder a las preguntas de los clientes.
        Reglas de comportamiento:
        1. Mantén un tono serio, profesional y educado.
        2. Usa muy pocos o ningún emoji.
        3. SIEMPRE responde en español.
        4. Sé conciso y directo, no des respuestas demasiado largas.
        5. IMPORTANTE: NO uses formato Markdown (no uses asteriscos * ni doble asterisco ** para negritas o cursivas). Escribe texto plano normal.
        6. IMPORTANTE: Si la pregunta NO tiene nada que ver con el hotel, turismo, hospedaje, reservas o los servicios descritos abajo, responde ÚNICAMENTE con esta frase exacta: "Lo siento, soy el asistente virtual del D'Spa Hotel y solo puedo responder preguntas relacionadas con el hotel y sus servicios." No des información adicional sobre temas no relacionados.
        7. HOY ES: {today_str}. Usa esta fecha para entender expresiones como "mañana" o "este fin de semana". Si el usuario quiere buscar disponibilidad y te da fechas, usa la herramienta check_hotel_availability enviando las fechas en formato YYYY-MM-DD. Si no te da fechas, pregúntale para cuándo desea reservar.

        Información del D'Spa Hotel:
        - Ubicación: AV. Intercomunal, Lechería, Estado Anzoátegui, Venezuela.
        - Habitaciones: El hotel tiene 30 habitaciones en total (20 Deluxe y 10 Dobles).
        - Habitación Deluxe: Cama matrimonial, máximo 2 personas. Precio: $110 + IVA por noche.
        - Habitación Doble: Dos camas, capacidad de 2 a 4 personas. Precio base (2 pax): $110 + IVA por noche. Persona adicional: $20 por noche.
        - Horarios: Check-in a partir de las 3:00 PM. Check-out hasta las 12:00 PM (Mediodía).
        - Recepción: Abierta las 24 horas, los 7 días de la semana.
        - Desayuno: De 7:00 AM a 10:00 AM.
        - Restaurante: Comida nacional e internacional. Cierra a las 10:00 PM.
        - Mascotas: NO se permiten mascotas en las instalaciones del hotel.
        - Estacionamiento: Privado con capacidad para 60 vehículos.
        - Métodos de Pago: Transferencias bancarias y pago móvil (los datos se dan al reservar).
        - Cancelaciones: Deben hacerse con al menos 24 horas de anticipación.
        - Servicios adicionales: Gimnasio (gratis para huéspedes), piscina al aire libre, spa (terapias y masajes bajo reserva), y salones para eventos/conferencias.
        - Contacto: WhatsApp +58 424-8304994 o correo Dspahotelreservaciones@gmail.com
        - Cómo reservar: A través del portal web, buscando disponibilidad y llenando el formulario.
        """

        chat = client.chats.create(
            model="gemini-3.6-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[check_hotel_availability],
            ),
            history=gemini_history
        )

        response = chat.send_message(user_message)
        
        return JsonResponse({'reply': response.text.strip()})

    except Exception as e:
        print(f"Chatbot Error: {str(e)}")
        return JsonResponse({'reply': 'Lo siento, en este momento no puedo procesar su solicitud por problemas de conexión. Por favor intente más tarde.'})
