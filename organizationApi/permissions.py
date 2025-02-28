from rest_framework import permissions

class IsOrganizer(permissions.BasePermission):
    """
    Custom permission to only allow organizers to perform certain actions.
    """
    def has_permission(self, request, view):
        # Check if user is authenticated and is an organizer
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_organizer
        )

    def has_object_permission(self, request, view, obj):
        # Check if user is the organizer of the specific object
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_organizer and
            obj.organizer == request.user
        )
