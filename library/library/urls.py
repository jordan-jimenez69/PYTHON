# DEPRECATED: This urls module belonged to the old layout. The project now uses
# `library_project.urls` as the root URLconf. Keep this file only for reference.

from django.urls import path
from django.http import HttpResponse

urlpatterns = [
    path('', lambda request: HttpResponse('Deprecated: use the new project root (library_project).')),
]

