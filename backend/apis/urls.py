"""erp URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include, re_path
from rest_framework.routers import DefaultRouter


import books.apis
import stores.apis
import accounts.apis
import authorities.apis


class OptionalRouter(DefaultRouter):
    def __init__(self):
        super().__init__()
        self.trailing_slash = '/?'


router = OptionalRouter()
router.register(r"categories", books.apis.CategoryViewSet, basename="category")
router.register(r"issues", books.apis.IssueViewSet, basename="issue")
router.register(r"bookmarks", books.apis.BookmarkViewSet, basename="bookmark")
router.register(r"banners", books.apis.BannerViewSet, basename="banner")
# router.register(r"previews", books.apis.PreviewViewSet, basename="preview")
router.register(r"assets", books.apis.AssetViewSet, basename="asset")
router.register(r"contracts", books.apis.ContractViewSet, basename="contract")

router.register(r"trades", stores.apis.TradeViewSet, basename="trade")
router.register(r"transactions", stores.apis.TransactionViewSet, basename="transaction")

# router.register(r"users", accounts.apis.UserViewSet, basename='user')
router.register(r"social-medias", accounts.apis.SocialMediaViewSet, basename="social-media")

urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'login', accounts.apis.LoginAPIView.as_view(), name='login'),
    re_path(r'logout', accounts.apis.LogoutAPIView.as_view(), name='logout'),
    re_path(r'nonce', accounts.apis.NonceAPIView.as_view(), name='nonce'),
    re_path(r'permissions', authorities.apis.PermissionAPIView.as_view(), name='permission'),
]
