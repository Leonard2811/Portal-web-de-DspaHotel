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
function toggleChatbot() {
    const container = document.getElementById('chatbotContainer');
    if (container) {
        container.classList.toggle('active');
    }
}

function askBot(key) {
    const text = getQuestionText(key);
    if (text) {
        document.getElementById('chatbotInput').value = text;
        sendChatMessage();
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
        'precios': 'Cuales son los precios?',
        'desayuno': 'Cual es el horario de desayuno?',
        'restaurante': 'Cual es el horario del restaurante?',
    };
    return questions[key] || key;
}

let chatHistory = [];

function sendChatMessage() {
    const input = document.getElementById('chatbotInput');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    addChatMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    const messagesContainer = document.getElementById('chatbotMessages');
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'chatbot-msg bot';
    typingIndicator.id = 'chatbotTypingIndicator';
    typingIndicator.innerHTML = '<span class="typing-dots"><span>.</span><span>.</span><span>.</span></span>';
    messagesContainer.appendChild(typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Send to API
    fetch('/api/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message, history: chatHistory })
    })
    .then(response => response.json())
    .then(data => {
        const indicator = document.getElementById('chatbotTypingIndicator');
        if (indicator) indicator.remove();
        
        if (data.reply) {
            chatHistory.push({ role: 'user', text: message });
            chatHistory.push({ role: 'bot', text: data.reply });
            addChatMessage(data.reply, 'bot');
        } else {
            addChatMessage('Lo siento, ocurrió un error.', 'bot');
        }
    })
    .catch(error => {
        const indicator = document.getElementById('chatbotTypingIndicator');
        if (indicator) indicator.remove();
        addChatMessage('Error de conexión. Intente más tarde.', 'bot');
    });
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

    fetch(`/api/search-availability/?check_in=${checkIn}&check_out=${checkOut}&adults=${adults}&children=0`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let html = '';

                if (data.deluxe_count === 0 && data.doble_count === 0) {
                    html = '<div class="col-12"><div class="alert alert-warning text-center"><i class="fas fa-exclamation-circle me-2"></i>No hay habitaciones disponibles para las fechas seleccionadas. Intente con otras fechas.</div></div>';
                } else {
                    // Summary
                    html += `<div class="col-12 mb-3">
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle me-2"></i>
                            <strong>${data.deluxe_count + data.doble_count}</strong> habitaciones disponibles para <strong>${data.nights}</strong> noche(s)
                        </div>
                    </div>`;

                    // Deluxe rooms
                    if (data.deluxe_count > 0 && data.deluxe_room) {
                        html += '<div class="col-12"><h5 class="mb-3"><i class="fas fa-bed me-2"></i>Habitaciones Deluxe</h5></div>';
                        html += createAvailabilityCard(data.deluxe_room, 'Deluxe', data.nights, data.deluxe_count);
                    }

                    // Doble rooms
                    if (data.doble_count > 0 && data.doble_room) {
                        html += '<div class="col-12 mt-3"><h5 class="mb-3"><i class="fas fa-bed me-2"></i>Habitaciones Dobles</h5></div>';
                        html += createAvailabilityCard(data.doble_room, 'Doble', data.nights, data.doble_count);
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
    const extraFee = parseFloat(room.extra_guest_fee || 0);
    const extraInfo = extraFee > 0 ? `<div class="mt-1"><small><i class="fas fa-info-circle me-1"></i>Persona adicional: $${extraFee}/noche</small></div>` : '';
    return `
        <div class="col-lg-6 col-md-6">
            <div class="booking-room-card">
                <div class="booking-room-header">
                    <h5>Habitación ${typeName}</h5>
                    <span class="badge bg-success" style="font-size: 0.9rem;">${count} disponible(s)</span>
                </div>
                <div class="booking-room-body">
                    <p class="mb-2">${room.description}</p>
                    <div class="booking-room-price">
                        <div><strong>Precio por noche:</strong> $${room.price} <small>+ IVA</small></div>
                        <div><strong>Total ${nights} noche(s):</strong> <span style="color: var(--color-gold); font-weight: 700; font-size: 1.1rem;">$${room.total} <small>+ IVA</small></span></div>
                        ${extraInfo}
                    </div>
                    <div class="booking-room-capacity">
                        <i class="fas fa-user-friends me-1"></i> ${room.capacity_adults} personas max.
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

    // Close navbar on mobile after click (except for dropdown toggles)
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link:not(.dropdown-toggle)');
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
