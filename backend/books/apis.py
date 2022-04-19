from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from utils.views import BaseViewSet
from . import models, serializers, filters
from .pdf_handler import PDFHandler

from authorities.permissions import IsOwner, IsPublisher


class CategoryViewSet(BaseViewSet):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer

    http_method_names = ['get']


class IssueViewSet(BaseViewSet):
    queryset = models.Issue.objects.all()
    serializer_class = serializers.IssueSerializer
    search_fields = ['name', 'author_name', 'publisher__name', 'publisher__account_addr', 'desc']

    http_method_names = ['get', 'post', 'update', 'patch', 'head', 'options']

    def create(self, request, *args, **kwargs):
        b_serializer = self.get_serializer(data=request.data, serializer_class=serializers.IssueBuildSerializer)
        b_serializer.is_valid(raise_exception=True)
        obj_issue = self.perform_create(b_serializer)

        serializer = self.get_serializer(obj_issue, many=False)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        kwargs['serializer_class'] = serializers.IssueListSerializer
        return super().list(request, *args, **kwargs)


class BookmarkViewSet(BaseViewSet):
    queryset = models.Bookmark.objects.all()
    serializer_class = serializers.BookmarkSerializer
    http_method_names = ['patch']


class BannerViewSet(BaseViewSet):
    queryset = models.Banner.objects.all()
    serializer_class = serializers.BannerSerializer

    http_method_names = ['get']


class PreviewViewSet(BaseViewSet):
    queryset = models.Preview.objects.all()
    serializer_class = serializers.PreviewSerializer


class AssetViewSet(BaseViewSet):
    permission_classes = [IsOwner]
    queryset = models.Asset.objects.all()
    serializer_class = serializers.AssetSerializer
    filterset_class = filters.AssetFilter
    http_method_names = ['get']

    @action(methods=['GET'], detail=True, url_path='read')
    def read(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.file:
            # get zip file from nft.storage
            file = PDFHandler().get_pdf(instance.issue.token_url, instance.issue.token)
            instance.file = file
            instance.save()
        return Response({'file': request.build_absolute_uri(instance.file.url)})


class ContractViewSet(BaseViewSet):
    permission_classes = [IsPublisher]
    queryset = models.Contract.objects.all()
    serializer_class = serializers.ContractSerializer


# class FragmentViewSet(BaseViewSet):
#     queryset = models.Fragment.objects.all()
#     serializer_class = serializers.FragmentSerializer
