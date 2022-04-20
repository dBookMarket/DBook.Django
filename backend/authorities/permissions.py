from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions, SAFE_METHODS, IsAdminUser


class IsOwner(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and hasattr(obj, 'user') and obj.user == request.user)


class IsPublisher(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            ((hasattr(obj, 'publisher') and obj.publisher == request.user) or
             (hasattr(obj, 'issue') and obj.issue.publisher == request.user))
        )


class ObjectPermissionsOrReadOnly(DjangoObjectPermissions):
    # authenticated_users_only = False

    def has_permission(self, request, view):
        """
        All users could read
        Only user who has perms could change/delete objects
        """
        is_authenticated = bool(request.user and request.user.is_authenticated)
        can_read = bool(request.method in SAFE_METHODS)
        return bool(can_read or (is_authenticated and super().has_permission(request, view)))


class IsAdminUserOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        return bool(request.method in SAFE_METHODS or super().has_permission(request, view))
