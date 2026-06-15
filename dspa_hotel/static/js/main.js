/* ====================================
   D'Spa Hotel - Main JavaScript
   ==================================== */

// ========== Navbar Scroll Effect ==========
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('mainNavbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
});

// ========== Smooth Scroll ==========
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// ========== Chatbot ==========
const chatbotResponses = {
    'tipos_habitaciones': 'Contamos con Habitaciones Deluxe Matrimoniales y Dobles, equipadas con bano privado, TV, caja fuerte, closet y terraza.',
    'servicios': 'Ofrecemos hospedaje, restaurante, gimnasio, spa, sauna, jacuzzi, piscina, salones para eventos y estacionamiento privado.',
    'ubicacion': 'Estamos en AV. Intercomunal, Lecheria, Estado Anzoategui, Venezuela.',
    'reservar': 'Debe registrarse en nuestro portal, buscar disponibilidad y completar el formulario de reservacion.',
    'mascotas': 'Por politicas de higiene y confort, no aceptamos mascotas.',
    'estacionamiento': 'Si, contamos con estacionamiento privado con capacidad para 60 vehiculos.',
    'horario': 'Nuestro servicio de recepcion opera las 24 horas del dia, los 7 dias de la semana.',
    'pago': 'Aceptamos transferencias bancarias y pago movil. Los datos bancarios se proporcionan al momento de la reservacion.',
    'cancelacion': 'Las cancelaciones deben realizarse con al menos 24 horas de anticipacion.',
    'checkin': 'El check-in es a partir de las 2:00 PM y el check-out hasta las 12:00 PM.',
};

function toggleChatbot() {
    const container = document.getElementById('chatbotContainer');
    if (container) {
        container.classList.toggle('active');
    }
}

function askBot(key) {
    const response = chatbotResponses[key];
    if (response) {
        addChatMessage(getQuestionText(key), 'user');
        setTimeout(() => {
            addChatMessage(response, 'bot');
        }, 500);
    }
}

function getQuestionText(key) {
    const questions = {
        'tipos_habitaciones': 'Que tipos de habitaciones tienen?',
        'servicios': 'Que servicios incluye el hotel?',
        'ubicacion': 'Donde estan ubicados?',
        'reservar': 'Como puedo reservar?',
        'mascotas': 'Aceptan mascotas?',
        'estacionamiento': 'Tienen estacionamiento?',
        'horario': 'Cual es el horario de recepcion?',
        'pago': 'Que metodos de pago aceptan?',
        'cancelacion': 'Cual es la politica de cancelacion?',
        'checkin': 'Cual es el horario de check-in?',
    };
    return questions[key] || key;
}

function sendChatMessage() {
    const input = document.getElementById('chatbotInput');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    addChatMessage(message, 'user');
    input.value = '';

    setTimeout(() => {
        const response = findBestResponse(message);
        addChatMessage(response, 'bot');
    }, 600);
}

function findBestResponse(message) {
    const msg = message.toLowerCase();

    if (msg.includes('habitacion') || msg.includes('cuarto') || msg.includes('tipo')) {
        return chatbotResponses['tipos_habitaciones'];
    }
    if (msg.includes('servicio') || msg.includes('ofrecen') || msg.includes('incluye')) {
        return chatbotResponses['servicios'];
    }
    if (msg.includes('ubicacion') || msg.includes('donde') || msg.includes('direccion') || msg.includes('llegar')) {
        return chatbotResponses['ubicacion'];
    }
    if (msg.includes('reservar') || msg.includes('reservacion') || msg.includes('booking')) {
        return chatbotResponses['reservar'];
    }
    if (msg.includes('mascota') || msg.includes('perro') || msg.includes('gato') || msg.includes('animal')) {
        return chatbotResponses['mascotas'];
    }
    if (msg.includes('estacionamiento') || msg.includes('parking') || msg.includes('carro') || msg.includes('vehiculo')) {
        return chatbotResponses['estacionamiento'];
    }
    if (msg.includes('horario') || msg.includes('hora') || msg.includes('abierto')) {
        return chatbotResponses['horario'];
    }
    if (msg.includes('pago') || msg.includes('pagar') || msg.includes('transferencia') || msg.includes('precio')) {
        return chatbotResponses['pago'];
    }
    if (msg.includes('cancelar') || msg.includes('cancelacion')) {
        return chatbotResponses['cancelacion'];
    }
    if (msg.includes('check-in') || msg.includes('checkin') || msg.includes('check-out') || msg.includes('checkout') || msg.includes('entrada') || msg.includes('salida')) {
        return chatbotResponses['checkin'];
    }
    if (msg.includes('spa') || msg.includes('masaje') || msg.includes('relajacion')) {
        return 'Contamos con servicio de spa con tratamientos corporales, faciales y terapias de relajacion. Puede reservar su sesion a traves de nuestro portal o contactarnos por WhatsApp.';
    }
    if (msg.includes('gym') || msg.includes('gimnasio') || msg.includes('ejercicio')) {
        return 'Nuestro gimnasio cuenta con equipos de ultima generacion y entrenadores certificados. Esta disponible para todos los huespedes del hotel.';
    }
    if (msg.includes('restaurante') || msg.includes('comida') || msg.includes('comer') || msg.includes('desayuno')) {
        return 'Nuestro restaurante ofrece cocina nacional e internacional con ingredientes frescos. El desayuno esta incluido para huespedes del hotel.';
    }
    if (msg.includes('piscina') || msg.includes('nadar')) {
        return 'Contamos con piscina al aire libre con servicio de bar y ambiente tropical, disponible para huespedes del hotel.';
    }
    if (msg.includes('evento') || msg.includes('salon') || msg.includes('conferencia') || msg.includes('reunion')) {
        return 'Disponemos de salones versatiles para eventos corporativos, conferencias, reuniones y celebraciones. Contactenos para cotizacion personalizada.';
    }
    if (msg.includes('whatsapp') || msg.includes('contacto') || msg.includes('telefono') || msg.includes('llamar')) {
        return 'Puede contactarnos por WhatsApp al +58 424-8304994 o por correo a Dspahotelreservaciones@gmail.com. Estamos para servirle.';
    }
    if (msg.includes('hola') || msg.includes('buenas') || msg.includes('buenos')) {
        return 'Bienvenido a D\'Spa Hotel. En que podemos ayudarle? Puede seleccionar una pregunta rapida o escribir su consulta.';
    }
    if (msg.includes('gracias') || msg.includes('thanks')) {
        return 'Con gusto. Si tiene alguna otra consulta, no dude en preguntar. Sera un placer atenderle en D\'Spa Hotel.';
    }

    return 'Gracias por su consulta. Para informacion mas detallada, le invitamos a contactarnos por WhatsApp al +58 424-8304994 o por correo a Dspahotelreservaciones@gmail.com.';
}

function addChatMessage(text, sender) {
    const container = document.getElementById('chatbotMessages');
    if (!container) return;

    const msg = document.createElement('div');
    msg.className = `chatbot-msg ${sender}`;
    msg.textContent = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

// ========== Search Rooms (Home Page) ==========
function searchRooms() {
    const checkIn = document.getElementById('check_in').value;
    const checkOut = document.getElementById('check_out').value;
    const adults = document.getElementById('adults').value;
    const children = document.getElementById('children').value;

    if (!checkIn || !checkOut) {
        alert('Por favor seleccione las fechas de check-in y check-out.');
        return;
    }

    if (new Date(checkOut) <= new Date(checkIn)) {
        alert('La fecha de check-out debe ser posterior al check-in.');
        return;
    }

    const resultsDiv = document.getElementById('availabilityResults');
    const container = document.getElementById('resultsContainer');

    if (!resultsDiv || !container) return;

    // Show loading
    container.innerHTML = '<div class="col-12 text-center py-4"><div class="spinner-border text-secondary" role="status"><span class="visually-hidden">Buscando...</span></div><p class="mt-2 text-muted">Buscando disponibilidad...</p></div>';
    resultsDiv.style.display = 'block';

    fetch(`/api/search-availability/?check_in=${checkIn}&check_out=${checkOut}&adults=${adults}&children=${children}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let html = '';

                if (data.matrimonial_count === 0 && data.double_count === 0) {
                    html = '<div class="col-12"><div class="alert alert-warning text-center"><i class="fas fa-exclamation-circle me-2"></i>No hay habitaciones disponibles para las fechas seleccionadas. Intente con otras fechas.</div></div>';
                } else {
                    // Summary
                    html += `<div class="col-12 mb-3">
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle me-2"></i>
                            <strong>${data.matrimonial_count + data.double_count}</strong> habitaciones disponibles para <strong>${data.nights}</strong> noche(s)
                        </div>
                    </div>`;

                    // Matrimonial rooms
                    if (data.matrimonial_count > 0 && data.matrimonial_room) {
                        html += '<div class="col-12"><h5 class="mb-3"><i class="fas fa-bed me-2"></i>Habitaciones Deluxe Matrimonial</h5></div>';
                        html += createAvailabilityCard(data.matrimonial_room, 'Deluxe Matrimonial', data.nights, data.matrimonial_count);
                    }

                    // Double rooms
                    if (data.double_count > 0 && data.double_room) {
                        html += '<div class="col-12 mt-3"><h5 class="mb-3"><i class="fas fa-bed me-2"></i>Habitaciones Deluxe Doble</h5></div>';
                        html += createAvailabilityCard(data.double_room, 'Deluxe Doble', data.nights, data.double_count);
                    }
                }

                container.innerHTML = html;
            } else {
                container.innerHTML = '<div class="col-12"><div class="alert alert-danger">Error al buscar disponibilidad. Intente nuevamente.</div></div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = '<div class="col-12"><div class="alert alert-danger">Error de conexion. Intente nuevamente.</div></div>';
        });
}

function createAvailabilityCard(room, typeName, nights, count) {
    return `
        <div class="col-lg-6 col-md-6">
            <div class="booking-room-card">
                <div class="booking-room-header">
                    <h5>${typeName}</h5>
                    <span class="badge bg-success" style="font-size: 0.9rem;">${count} disponible(s)</span>
                </div>
                <div class="booking-room-body">
                    <p class="mb-2">${room.description}</p>
                    <div class="booking-room-price">
                        <div><strong>Precio por noche:</strong> $${room.price}</div>
                        <div><strong>Total ${nights} noche(s):</strong> <span style="color: var(--color-gold); font-weight: 700; font-size: 1.1rem;">$${room.total}</span></div>
                    </div>
                    <div class="booking-room-capacity">
                        <i class="fas fa-user-friends me-1"></i> ${room.capacity_adults} adultos, ${room.capacity_children} nino(s)
                    </div>
                </div>
                <a href="/reservations/booking/?room_id=${room.id}" class="btn btn-reservation w-100" style="border-radius: 0 0 12px 12px;">
                    <i class="fas fa-concierge-bell me-1"></i> Reservar
                </a>
            </div>
        </div>`;
}

// ========== Date Validation ==========
document.addEventListener('DOMContentLoaded', function() {
    // Set min dates
    const today = new Date().toISOString().split('T')[0];
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];

    const checkInInputs = document.querySelectorAll('input[name="check_in"], #check_in, #booking_checkin');
    const checkOutInputs = document.querySelectorAll('input[name="check_out"], #check_out, #booking_checkout');

    checkInInputs.forEach(input => {
        if (!input.value) input.value = today;
        input.min = today;
        input.addEventListener('change', function() {
            const nextDay = new Date(this.value);
            nextDay.setDate(nextDay.getDate() + 1);
            const nextDayStr = nextDay.toISOString().split('T')[0];
            checkOutInputs.forEach(co => {
                co.min = nextDayStr;
                if (co.value && co.value <= this.value) {
                    co.value = nextDayStr;
                }
            });
        });
    });

    checkOutInputs.forEach(input => {
        if (!input.value) input.value = tomorrow;
        input.min = tomorrow;
    });

    // Close navbar on mobile after click
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navCollapse = document.querySelector('.navbar-collapse');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (navCollapse && navCollapse.classList.contains('show')) {
                new bootstrap.Collapse(navCollapse).hide();
            }
        });
    });

    // Add animation on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.service-card, .room-card, .value-card, .contact-card, .mv-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
});

// ========== Form Validation ==========
function validateReservationForm() {
    const checkIn = document.querySelector('input[name="check_in"]');
    const checkOut = document.querySelector('input[name="check_out"]');
    const terms = document.getElementById('termsCheck');

    if (checkIn && checkOut) {
        if (new Date(checkOut.value) <= new Date(checkIn.value)) {
            alert('La fecha de check-out debe ser posterior al check-in.');
            return false;
        }
    }

    if (terms && !terms.checked) {
        alert('Debe aceptar los terminos y condiciones.');
        return false;
    }

    return true;
}

// ========== Confirmation Dialogs ==========
document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function(e) {
        if (!confirm(this.dataset.confirm)) {
            e.preventDefault();
        }
    });
});
