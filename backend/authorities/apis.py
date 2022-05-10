from rest_framework.response import Response
from rest_framework.authtoken.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import AnonymousUser, Permission


class PermissionAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        has_perm = False
        if request.user is not None and not isinstance(request.user, AnonymousUser):
            try:
                issue_perm = Permission.objects.get(codename='add_issue')
                has_perm = request.user.has_perm(issue_perm)
            except Permission.DoesNotExist:
                has_perm = False
        return Response({'has_issue_perm': has_perm})
