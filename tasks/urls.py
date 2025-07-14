from django.urls import path
from . import views
from .views import (
    view_log_file,
    download_log_file,
)

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.create_task, name='create_task'),
    path('delete/<int:pk>/', views.delete_task, name='delete_task'),
    path('register/', views.register, name='register'),
    path('lists/create/', views.create_tasklist, name='create_tasklist'),
    path('lists/share/', views.share_tasklist, name='share_tasklist'),
    path('log-error/', views.log_error_view, name='log_error'),
]

urlpatterns += [
    path('logs/', view_log_file, name='view_log_file'),
    path('logs/download/', download_log_file, name='download_log_file'),
] 