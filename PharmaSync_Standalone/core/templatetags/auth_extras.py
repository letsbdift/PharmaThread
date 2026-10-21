from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Checks if a user belongs to a specific group.
    Usage in templates: {% if request.user|has_group:"Admin" %}
    """
    if not user.is_authenticated:
        return False
    # To prevent hitting the database for every single check, it might be better to prefetch
    # but for this scale, simply checking user.groups is fine.
    return user.groups.filter(name=group_name).exists()
