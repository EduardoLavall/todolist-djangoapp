from django.db import models

# 🎯 Create your models here.

class Task(models.Model):
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
    due_date = models.DateField()
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=ONGOING)
    is_completed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # 🔄 Automatically update is_completed based on status
        self.is_completed = (self.status == self.COMPLETED)
        super().save(*args, **kwargs)

    def __str__(self):
        # 🏷️ Return the task title when converting to string
        return self.title
