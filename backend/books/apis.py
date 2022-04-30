from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from utils.views import BaseViewSet
from . import models, serializers, filters
from stores.models import Trade
from .pdf_handler import PDFHandler
from django.db.transaction import atomic
from .file_service_connector import FileServiceConnector
from utils.enums import IssueStatus
from authorities.permissions import IsOwner, IsPublisher, ObjectPermissionsOrReadOnly, IsAdminUserOrReadOnly


class CategoryViewSet(BaseViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    filterset_class = filters.CategoryFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class IssueViewSet(BaseViewSet):
    permission_classes = [ObjectPermissionsOrReadOnly]
    queryset = models.Issue.objects.all()
    serializer_class = serializers.IssueSerializer
    filterset_class = filters.IssueFilter
    search_fields = ['name', 'author_name', 'publisher__name', 'publisher__account_addr', 'desc', 'category__name']

    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_permissions(self):
        if self.action == 'retrieve_current_issue':
            self.permission_classes = [IsPublisher]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        obj = queryset.filter(publisher=request.user).exclude(status=IssueStatus.SUCCESS.value).first()
        if obj:
            raise ValidationError({'detail': 'You are issuing a book, please finish it firstly.'})
        return super().create(request, *args, **kwargs)

    # def list(self, request, *args, **kwargs):
    #     serializer_class = serializers.IssueListSerializer
    #     queryset = self.filter_queryset(self.get_queryset())
    #     queryset = queryset.filter(status=IssueStatus.SUCCESS.value)
    #
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True, serializer_class=serializer_class)
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(queryset, many=True, serializer_class=serializer_class)
    #     return Response(serializer.data)
    #
    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     if instance.status != IssueStatus.SUCCESS.value:
    #         return Response(status=status.HTTP_404_NOT_FOUND)
    #     serializer = self.get_serializer(instance, many=False)
    #     return Response(serializer.data)

    def get_issuing_object(self):
        queryset = self.get_queryset()

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        # instance = get_object_or_404(self.get_queryset(), **{'pk': kwargs.get('pk')})
        # self.check_object_permissions(request, instance)
        instance = self.get_issuing_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(methods=['PATCH'], detail=True, url_path='trade')
    def trade(self, request, *args, **kwargs):
        """
        Call it when the file is uploaded.
        """
        # obj_issue = get_object_or_404(self.get_queryset(), **{'pk': kwargs.get('pk')})
        # self.check_object_permissions(request, obj_issue)
        obj_issue = self.get_issuing_object()
        if obj_issue.status == IssueStatus.SUCCESS.value:
            raise ValidationError(
                {'detail': 'The file uploading already has been finished successfully. '
                           'If you want to change it, you can re-upload a new one.'}
            )
        elif obj_issue.status != IssueStatus.UPLOADED.value:
            raise ValidationError({'detail': 'The file uploading is failure, or not finished.'})
        with atomic():
            pdf_handler = PDFHandler(obj_issue.file.path)
            # 1, update status
            obj_issue.status = IssueStatus.SUCCESS.value
            obj_issue.save()
            # 2, save preview
            obj_preview = models.Preview.objects.create(issue=obj_issue)
            pre_file = pdf_handler.get_preview_doc(from_page=obj_preview.start_page - 1,
                                                   to_page=obj_preview.start_page + obj_preview.n_pages - 2)
            obj_preview.file = pre_file
            obj_preview.save()
            # 3, save trade
            Trade.objects.create(issue=obj_issue, price=obj_issue.price, amount=obj_issue.amount,
                                 user=obj_issue.publisher, first_release=True)
            # 4, asset
            models.Asset.objects.create(user=obj_issue.publisher, issue_id=obj_issue.id, amount=obj_issue.amount)
        serializer = self.get_serializer(obj_issue, many=False)
        # delete temporary file
        if obj_issue.file:
            obj_issue.file.delete()
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='current')
    def retrieve_current_issue(self, request, *args, **kwargs):
        """
        Fetch the current issue which the user is building. If not, will return 404
        """
        queryset = self.get_queryset()
        issue = queryset.filter(publisher=request.user).exclude(status=IssueStatus.SUCCESS.value).first()
        serializer = self.get_serializer(issue)
        return Response(serializer.data)


class BookmarkViewSet(BaseViewSet):
    queryset = models.Bookmark.objects.all()
    serializer_class = serializers.BookmarkSerializer
    http_method_names = ['patch']


class BannerViewSet(BaseViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    queryset = models.Banner.objects.all()
    serializer_class = serializers.BannerSerializer
    filterset_class = filters.BannerFilter


# class PreviewViewSet(BaseViewSet):
#     queryset = models.Preview.objects.all()
#     serializer_class = serializers.PreviewSerializer


class AssetViewSet(BaseViewSet):
    permission_classes = [IsOwner]
    queryset = models.Asset.objects.all()
    serializer_class = serializers.AssetSerializer
    filterset_class = filters.AssetFilter
    http_method_names = ['get']

    @action(methods=['GET'], detail=True, url_path='read')
    def read(self, request, *args, **kwargs):
        instance = self.get_object()
        urls = []
        if instance.issue.cid:
            urls = FileServiceConnector().get_file_urls(instance.issue.cid)
        return Response({'files': urls})


class ContractViewSet(BaseViewSet):
    permission_classes = [IsPublisher]
    queryset = models.Contract.objects.all()
    serializer_class = serializers.ContractSerializer
