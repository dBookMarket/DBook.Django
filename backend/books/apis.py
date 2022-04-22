from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import permission_classes as dec_permission_classes
from django.contrib.auth.decorators import login_required
from utils.views import BaseViewSet
from . import models, serializers, filters
from stores.models import Trade
from .pdf_handler import PDFHandler
from django.db.transaction import atomic
from .file_service_connector import FileServiceConnector
from utils.enums import FileUploadStatus
from authorities.permissions import IsOwner, IsPublisher, ObjectPermissionsOrReadOnly, IsAdminUserOrReadOnly


class CategoryViewSet(BaseViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    filterset_class = filters.CategoryFilter


class IssueViewSet(BaseViewSet):
    permission_classes = [ObjectPermissionsOrReadOnly]
    queryset = models.Issue.objects.all()
    serializer_class = serializers.IssueSerializer
    filterset_class = filters.IssueFilter
    search_fields = ['name', 'author_name', 'publisher__name', 'publisher__account_addr', 'desc']

    http_method_names = ['get', 'post', 'update', 'patch', 'head', 'options']

    def get_permissions(self):
        if self.action in {'list_private_issues', 'retrieve_private_issue'}:
            self.permission_classes = [IsPublisher]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj_issue = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # send a celery task to upload file to nft.storage
        try:
            result = FileServiceConnector().upload_file(obj_issue.file.path)
            if result:
                obj_issue.task_id = result.task_id
                obj_issue.status = FileUploadStatus.UPLOADING.value
                obj_issue.save()
        except Exception as e:
            print(f'Exception when create issue: {e}')
            obj_issue.status = FileUploadStatus.FAILURE.value
            obj_issue.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        serializer_class = serializers.IssueListSerializer
        queryset = self.filter_queryset(self.get_queryset())
        # only show successful issues
        queryset = queryset.filter(status=FileUploadStatus.SUCCESS.value)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, serializer_class=serializer_class)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, serializer_class=serializer_class)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != FileUploadStatus.SUCCESS.value:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance, many=False)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='private')
    def list_private_issues(self, request, *args, **kwargs):
        """
        Show publisher's issues all built
        """
        serializer_class = serializers.IssueListSerializer
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(publisher=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, serializer_class=serializer_class)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, serializer_class=serializer_class)
        return Response(serializer.data)

    @action(methods=['GET'], detail=True, url_path='private')
    def retrieve_private_issue(self, request, *args, **kwargs):
        """
        Show publisher's issue detail
        """
        instance = self.get_object()
        if instance.publisher != request.user:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance, many=False)
        return Response(serializer.data)

    @action(methods=['PATCH'], detail=True, url_path='trade')
    def trade(self, request, *args, **kwargs):
        """
        Call it when the file is uploaded.
        """
        obj_issue = self.get_object()
        if obj_issue.status != FileUploadStatus.UPLOADED.value:
            raise ValidationError({'detail': 'The file uploading is failure, or not finished.'})
        with atomic():
            pdf_handler = PDFHandler(obj_issue.file.path)
            # 1, update status
            obj_issue.status = FileUploadStatus.SUCCESS.value
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
