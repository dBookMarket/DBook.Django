"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.contrib import admin
from django.conf.urls import re_path
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.documentation import include_docs_urls

import apis.urls
from rest_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='D-BOOK API')

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('d-book-admin/', admin.site.urls),
    path(r'api/v1/', include(apis.urls)),
    path('api-doc/', include_docs_urls(title='api文档')),
    # re_path(r'^api-doc$', schema_view),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
] + static(settings.MEDIA_URL,
           document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL,
                                                       document_root=settings.STATIC_ROOT) + static(
    settings.ENCRYPTION_URL,
    document_root=settings.ENCRYPTION_ROOT)
