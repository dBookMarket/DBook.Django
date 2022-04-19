from rest_framework import viewsets
from rest_framework.response import Response


class BaseViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        return serializer.save()

    def perform_update(self, serializer):
        return serializer.save()

    def get_serializer(self, *args, **kwargs):
        serializer_class = kwargs.pop('serializer_class', self.get_serializer_class())
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        serializer_class = kwargs.pop('serializer_class', self.get_serializer_class())
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, serializer_class=serializer_class)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, serializer_class=serializer_class)
        return Response(serializer.data)
