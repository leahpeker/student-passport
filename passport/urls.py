"""API routes. Mounted under /api/ by config/urls.py."""

from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.me, name='me'),
    path('classrooms/', views.classrooms, name='classrooms'),
    path('classrooms/<int:pk>/digest/', views.classroom_digest, name='classroom-digest'),
    path('classrooms/<int:pk>/ask/', views.classroom_ask, name='classroom-ask'),
    path('students/<int:pk>/passport/', views.passport, name='passport'),
    path('students/<int:pk>/records/', views.records, name='records'),
    path('students/<int:pk>/digest/', views.digest, name='digest'),
    path('students/<int:pk>/ask/', views.ask, name='ask'),
    path('students/<int:pk>/input/', views.student_input, name='input'),
    path('students/<int:pk>/export/', views.export, name='export'),
]
