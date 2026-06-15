from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/search-availability/', views.search_availability, name='search_availability'),
    path('about/', views.about, name='about'),
    path('services/', views.services_view, name='services'),
    path('rooms/', views.rooms_view, name='rooms'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('contact/', views.contact, name='contact'),
    path('location/', views.location, name='location'),
    path('register/', views.register, name='register'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
