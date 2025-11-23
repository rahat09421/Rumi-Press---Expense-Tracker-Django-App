from .mixins import is_admin

def is_admin_flag(request):
    try:
        return { 'is_admin': is_admin(request.user) }
    except Exception:
        return { 'is_admin': False }