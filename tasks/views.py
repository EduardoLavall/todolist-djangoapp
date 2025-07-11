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
            # Preserve current filter and sort when redirecting
            return redirect_with_params('task_list', request.GET)
        else:
            # Handle inline editing
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id)
            form = TaskForm(request.POST, instance=task)
            if form.is_valid():
                form.save()
                # Preserve current filter and sort when redirecting
                # Check for filter parameters in POST data first, then GET
                params = {}
                if request.POST.get('filter_status'):
                    params['status'] = request.POST.get('filter_status')
                elif request.GET.get('status'):
                    params['status'] = request.GET.get('status')
                if request.POST.get('filter_sort'):
                    params['sort'] = request.POST.get('filter_sort')
                elif request.GET.get('sort'):
                    params['sort'] = request.GET.get('sort')
                return redirect_with_params('task_list', params)
    else:
        form = TaskForm()
    
    # Get filter and sort parameters from request
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'due_date')
    
    # Start with all tasks
    tasks = Task.objects.all()
    
    # Apply status filter if specified
    if status_filter == 'completed':
        tasks = tasks.filter(status='completed')
    elif status_filter == 'ongoing':
        tasks = tasks.filter(status='ongoing')
    # If status_filter is empty or invalid, show all tasks
    
    # Apply sorting
    if sort_by == 'priority':
        # Order by priority: high, medium, low
        tasks = tasks.annotate(
            priority_order=Case(
            When(priority='high', then=Value(0)),
            When(priority='medium', then=Value(1)),
            When(priority='low', then=Value(2)),
            output_field=IntegerField()
            )
            ).order_by('priority_order')
        
    elif sort_by == 'status':
        # Order by status: ongoing, completed
        tasks = tasks.annotate(
            status_order=Case(
            When(status='ongoing', then=Value(0)),
            When(status='completed', then=Value(1)),
            output_field=IntegerField()
            )
            ).order_by('status_order')

    else:
        # Default: order by due_date
        tasks = tasks.order_by('due_date')
    
    return render(request, 'tasks/task_list.html', {
        'tasks': tasks, 
        'form': form,
        'current_status_filter': status_filter,
        'current_sort': sort_by
    })

def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            # Preserve current filter and sort when redirecting
            params = {}
            if request.GET.get('status'):
                params['status'] = request.GET.get('status')
            if request.GET.get('sort'):
                params['sort'] = request.GET.get('sort')
            return redirect_with_params('task_list', params)
        # If invalid, render the task list with errors and show_modal
        sort_by = request.GET.get('sort', 'due_date')
        status_filter = request.GET.get('status', '')
        
        # Start with all tasks
        tasks = Task.objects.all()
        
        # Apply status filter if specified
        if status_filter == 'completed':
            tasks = tasks.filter(status='completed')
        elif status_filter == 'ongoing':
            tasks = tasks.filter(status='ongoing')
        
        # Apply sorting
        if sort_by == 'priority':
            tasks = tasks.annotate(
                priority_order=Case(
                    When(priority='high', then=Value(0)),
                    When(priority='medium', then=Value(1)),
                    When(priority='low', then=Value(2)),
                    output_field=IntegerField()
                )
            ).order_by('priority_order')
        elif sort_by == 'status':
            tasks = tasks.annotate(
                status_order=Case(
                    When(status='ongoing', then=Value(0)),
                    When(status='completed', then=Value(1)),
                    output_field=IntegerField()
                )
            ).order_by('status_order')
        else:
            tasks = tasks.order_by('due_date')
            
        return render(request, 'tasks/task_list.html', {
            'tasks': tasks,
            'form': form,
            'show_modal': True,
            'current_status_filter': status_filter,
            'current_sort': sort_by
        })
    # Always redirect to task list for GET requests
    return redirect('task_list')

def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        return redirect('task_list')
    return render(request, 'tasks/delete_task.html', {'task': task})

def redirect_with_params(view_name, params):
    """Helper function to redirect while preserving query parameters"""
    from django.urls import reverse
    url = reverse(view_name)
    if params:
        param_strings = []
        for key, value in params.items():
            if value:  # Only include non-empty values
                param_strings.append(f"{key}={value}")
        if param_strings:
            url += '?' + '&'.join(param_strings)
    return redirect(url)
