# from django.http.response import HttpResponseForbidden
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from utils.views import BaseViewSet
from . import models, serializers, filters
# from stores.models import Trade
# from .pdf_handler import PDFHandler
# from django.db.transaction import atomic
from .file_service_connector import FileServiceConnector
# from books.file_service_config import FileServiceConfig
# from utils.enums import IssueStatus
# from django.conf import settings
from authorities.permissions import ObjectPermissionsOrReadOnly
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from utils.cache import Cache


class DraftViewSet(BaseViewSet):
    # permission_classes = [DjangoObjectPermissions]
    queryset = models.Draft.objects.all()
    serializer_class = serializers.DraftSerializer
    filterset_class = filters.DraftFilter


class BookViewSet(BaseViewSet):
    # permission_classes = [DjangoObjectPermissions]
    queryset = models.Book.objects.all()
    serializer_class = serializers.BookSerializer
    filterset_class = filters.BookFilter

    def list(self, request, *args, **kwargs):
        kwargs['serializer_class'] = serializers.BookListingSerializer
        return super().list(request, *args, **kwargs)


class IssueViewSet(BaseViewSet):
    permission_classes = [ObjectPermissionsOrReadOnly]
    queryset = models.Issue.objects.all()
    serializer_class = serializers.IssueSerializer
    filterset_class = filters.IssueFilter
    search_fields = ['book__title', 'book__desc', 'book__author__name']


class BookmarkViewSet(BaseViewSet):
    queryset = models.Bookmark.objects.all()
    serializer_class = serializers.BookmarkSerializer
    http_method_names = ['patch', 'put']


class AssetViewSet(BaseViewSet):
    queryset = models.Asset.objects.all()
    serializer_class = serializers.AssetSerializer
    filterset_class = filters.AssetFilter
    http_method_names = ['get']

    @action(methods=['get'], detail=True, url_path='read')
    def read(self, request, *args, **kwargs):
        """
        0, check if the user has this book or not?
        1, fetch files from filecoin
        2, decrypt files
        3, merge files into pdf
        """
        obj = self.get_object()

        session_key = f'asset_{obj.book.id}'
        expire_time = 7 * 24 * 3600  # 1 week
        cache = Cache(request.session)
        path = cache.get(session_key)
        if path is None:
            encryption_key = models.EncryptionKey.objects.get(user=obj.book.author, book=obj.book)
            path = FileServiceConnector().download_file(obj.book.cid, encryption_key.key)
            cache.set(session_key, path, expire_time)

        url = request.build_absolute_uri(path)
        return Response({'url': url})


class WishlistViewSet(BaseViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = models.Wishlist.objects.all()
    serializer_class = serializers.WishlistSerializer
    filterset_class = filters.WishlistFilter
    http_method_names = ['post', 'delete', 'get']

    @action(methods=['get'], detail=False, url_path='current', permission_classes=[IsAuthenticated])
    def list_current(self, request, *args, **kwargs):
        """
        Fetch current user's wish list.
        """
        if not request.GET._mutable:
            request.GET._mutable = True
        request.GET['user'] = request.user
        return super().list(request, *args, **kwargs)

    @action(methods=['post'], detail=False, url_path='remove')
    def remove(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdvertisementViewSet(BaseViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = models.Advertisement.objects.all()
    serializer_class = serializers.AdvertiseSerializer
    filterset_class = filters.AdvertisementFilter
    http_method_names = ['get']
