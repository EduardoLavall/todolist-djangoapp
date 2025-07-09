from django.db import models

# Create your models here.

class Task(models.Model):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    PRIORITY_CHOICES = [
        (HIGH, 'High'),
        (MEDIUM, 'Medium'),
        (LOW, 'Low'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title
