"""URL configuration.

Everything that is not /admin/ or /api/ falls through to the React app, which
owns client-side routing.
"""

from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView

spa = TemplateView.as_view(template_name='index.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^(?!admin/|api/|static/).*$', spa, name='spa'),
]
