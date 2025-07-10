from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Case, When, IntegerField, Value
from .models import Task
from .forms import TaskForm

# Create your views here.

def task_list(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_completion':
            # Handle checkbox toggle
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id)
            is_completed = request.POST.get('is_completed') == '1'
            
            if is_completed:
                task.status = 'completed'
                task.is_completed = True
            else:
                task.status = 'ongoing'
                task.is_completed = False
            
            task.save()
            return redirect('task_list')
        else:
            # Handle inline editing
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id)
            form = TaskForm(request.POST, instance=task)
            if form.is_valid():
                form.save()
                return redirect('task_list')
    else:
        form = None
    
    # Get sort parameter from request
    sort_by = request.GET.get('sort', 'due_date')
    
    # Order tasks based on sort parameter
    if sort_by == 'priority':
        # Order by priority: high, medium, low
        tasks = Task.objects.annotate(
            priority_order=Case(
            When(priority='high', then=Value(0)),
            When(priority='medium', then=Value(1)),
            When(priority='low', then=Value(2)),
            output_field=IntegerField()
            )
            ).order_by('priority_order')
        
    elif sort_by == 'status':
        # Order by status: ongoing, completed
        tasks = Task.objects.annotate(
            status_order=Case(
            When(status='ongoing', then=Value(0)),
            When(status='completed', then=Value(1)),
            output_field=IntegerField()
            )
            ).order_by('status_order')

    else:
        # Default: order by due_date
        tasks = Task.objects.all().order_by('due_date')
    
    return render(request, 'tasks/task_list.html', {'tasks': tasks, 'form': form})

def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = TaskForm()
    
    return render(request, 'tasks/create_task.html', {'form': form})
