from django import forms
from django.forms import DateTimeInput
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'status']
        widgets = {
            'due_date': DateTimeInput(attrs={'type': 'datetime-local'}),
        } 