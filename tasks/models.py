from django.db import models
from django.contrib.auth.models import User

# 🎯 Create your models here.

class TaskList(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasklists')
    shared_with = models.ManyToManyField(User, related_name='shared_tasklists', blank=True)

    class Meta:
        unique_together = ('user', 'name')
        verbose_name = 'Task List'
        verbose_name_plural = 'Task Lists'

    def __str__(self):
        return self.name

class Task(models.Model):
    # 👤 User who owns this task
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    # 🚨 Priority levels for tasks: 🔴 High, 🟡 Medium, 🟢 Low
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    PRIORITY_CHOICES = [
        (HIGH, 'High'),
        (MEDIUM, 'Medium'),
        (LOW, 'Low'),
    ]
    # 📊 Status options for task progress
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    STATUS_CHOICES = [
        (ONGOING, 'Ongoing'),
        (COMPLETED, 'Completed'),
    ]
    # 📝 Task details: title, description, due date, priority, status, and completion status
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=ONGOING)
    is_completed = models.BooleanField(default=False)
    tasklist = models.ForeignKey('TaskList', on_delete=models.CASCADE, related_name='tasks')

    def save(self, *args, **kwargs):
        # 🔄 Automatically update is_completed based on status
        self.is_completed = (self.status == self.COMPLETED)
        super().save(*args, **kwargs)

    def __str__(self):
        # 🏷️ Return the task title when converting to string
        return self.title
