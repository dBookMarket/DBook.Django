from django.shortcuts import render, get_object_or_404
from .models import Issue


def share(request, issue_id):
    obj = get_object_or_404(Issue, pk=issue_id)
    redirect_url = request.GET.get('redirect_url', '')
    return render(request, 'books/share.html', {'issue': obj, 'redirect_url': redirect_url})
