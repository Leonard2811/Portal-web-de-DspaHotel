from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


def _get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registrar inicio de sesión de usuarios staff"""
    if user.is_staff:
        from .models import AuditLog
        AuditLog.objects.create(
            user=user,
            action='login',
            description=f'El usuario "{user.username}" ({user.get_full_name() or "Sin nombre"}) inició sesión en el sistema.',
            ip_address=_get_client_ip(request),
        )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Registrar cierre de sesión de usuarios staff"""
    if user and user.is_staff:
        from .models import AuditLog
        AuditLog.objects.create(
            user=user,
            action='logout',
            description=f'El usuario "{user.username}" ({user.get_full_name() or "Sin nombre"}) cerró sesión.',
            ip_address=_get_client_ip(request),
        )

