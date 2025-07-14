from django.contrib import admin
from .models import Task, TaskList

@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)

admin.site.register(Task)