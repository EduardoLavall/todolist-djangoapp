from django import forms
from django.forms import DateTimeInput
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task, TaskList

class TaskForm(forms.ModelForm):
    tasklist = forms.ModelChoiceField(
        queryset=TaskList.objects.none(),
        empty_label="Select a list",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'status', 'tasklist']
        widgets = {
            'due_date': DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['tasklist'].queryset = TaskList.objects.filter(user=user)
        
        # Style all fields with Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name not in ['due_date', 'tasklist']:  # these are already styled
                field.widget.attrs.update({
                    'class': 'form-control'
                })

class TaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'My Awesome List'
            })
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style all fields with Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name != 'email':  # email already styled
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': f'Enter your {field_name.replace("_", " ")}'
                })
            # Remove default help text for cleaner look
            field.help_text = ''
        
        # Custom placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['password1'].widget.attrs['placeholder'] = 'Create a password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm your password' 