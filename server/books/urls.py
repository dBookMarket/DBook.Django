from django.urls import re_path
from . import views

app_name = 'books'
urlpatterns = [
    re_path(r'share/(?P<issue_id>[^/.]+)/?', views.share, name='share')
]
