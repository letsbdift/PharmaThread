from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles=None):
    """
    Decorator for views that checks that the user belongs to one of the specified roles.
    If not, raises PermissionDenied (403).
    """
    if allowed_roles is None:
        allowed_roles = []
        
    def check_role(user):
        if not user.is_authenticated:
            return False
        # Superusers can bypass roles or they can just be in 'Admin' group.
        if user.is_superuser:
            return True
        if user.groups.filter(name__in=allowed_roles).exists():
            return True
        raise PermissionDenied

    return user_passes_test(check_role)
