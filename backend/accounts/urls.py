from django.urls import re_path
from . import views

app_name = 'accounts'
urlpatterns = [
    re_path(r'login-with-metamask', views.LoginWithMetaMaskView.as_view(), name='login-with-metamask'),
    re_path(r'issue-perm', views.IssuePermView.as_view(), name='issue-perm')
]
