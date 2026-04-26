from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Permission class to restrict access to staff and superuser accounts only.

    This centralizes admin authorization checks instead of manually checking
    `is_staff` or `is_superuser` in each view.
    """

    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)


def can_manage_user(actor, target):
    """
    Enforce safer moderation rules:
    - Staff can manage regular users only.
    - Only superusers can manage staff/superusers.
    """
    if not actor or not actor.is_authenticated:
        return False, "Authentication required."

    if not (actor.is_staff or actor.is_superuser):
        return False, "Admin privileges required."

    if actor == target:
        return False, "You cannot perform this action on yourself."

    if (target.is_superuser or target.is_staff) and not actor.is_superuser:
        return False, "Only superusers can manage staff or superuser accounts."

    return True, None
