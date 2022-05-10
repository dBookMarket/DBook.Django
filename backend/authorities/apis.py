from rest_framework.response import Response
from rest_framework.authtoken.views import APIView
from rest_framework.permissions import AllowAny


class PermissionAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        has_perm = False
        if request.user is not None:
            has_perm = request.user.has_perm('books.add_issue')
        return Response({'has_issue_perm': has_perm})
