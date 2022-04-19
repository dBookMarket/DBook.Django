from rest_framework.permissions import IsAuthenticated


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
