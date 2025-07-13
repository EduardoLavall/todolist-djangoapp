from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Case, When, IntegerField, Value
from django.http import JsonResponse
from django.contrib import messages
from .models import Task
from .forms import TaskForm, UserRegistrationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# Create your views here.

def register(request):
    if request.user.is_authenticated:
        return redirect('task_list')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, '🎉 Account created successfully! Please log in with your new credentials.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def task_list(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_completion':
            # Handle checkbox toggle
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, user=request.user)
            is_completed = request.POST.get('is_completed') == '1'
            
            try:
                if is_completed:
                    task.status = 'completed'
                    task.is_completed = True
                else:
                    task.status = 'ongoing'
                    task.is_completed = False
                
                task.save()
                
                # Check if this is an AJAX request
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    # Return JSON response for AJAX requests
                    return JsonResponse({
                        'success': True,
                        'status': task.status,
                        'is_completed': task.is_completed
                    })
                else:
                    # Regular form submission - redirect
                    return redirect_with_params('task_list', request.GET)
            except Exception as e:
                # Handle any errors during status update
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    # Return JSON response with error for AJAX requests
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to update task status. Please try again.'
                    }, status=400)
                else:
                    # Regular form submission - redirect (could be enhanced)
                    return redirect_with_params('task_list', request.GET)
        else:
            # Handle inline editing
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, user=request.user)
            form = TaskForm(request.POST, instance=task)
            if form.is_valid():
                task = form.save()
                
                # Check if this is an AJAX request
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    # Return JSON response for AJAX requests
                    return JsonResponse({
                        'success': True,
                        'task': {
                            'id': task.id,
                            'title': task.title,
                            'description': task.description or '',
                            'due_date': task.due_date.strftime('%b %d, %Y %I:%M %p'),
                            'due_date_local': task.due_date.strftime('%Y-%m-%dT%H:%M'),
                            'priority': task.priority,
                            'status': task.status,
                            'is_completed': task.is_completed
                        }
                    })
                else:
                    # Regular form submission - redirect
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
                # Form is invalid
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    # Return JSON response with errors for AJAX requests
                    return JsonResponse({
                        'success': False,
                        'errors': form.errors
                    })
                else:
                    # Regular form submission - render with errors
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
    status_filter = request.GET.get('status', 'ongoing')  # Default to 'ongoing' instead of empty string
    sort_by = request.GET.get('sort', 'due_date')
    
    # Start with tasks for the current user
    tasks = Task.objects.filter(user=request.user)
    
    # Apply status filter if specified
    if status_filter == 'completed':
        tasks = tasks.filter(status='completed')
    elif status_filter == 'ongoing':
        tasks = tasks.filter(status='ongoing')
    elif status_filter == 'all':
        # Show all tasks for the current user (no status filter applied)
        pass
    # If status_filter is 'ongoing' (default), filter for ongoing tasks
    # If status_filter is empty or invalid, show all tasks (fallback)
    
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
    
    # Check if this is an AJAX request for filtering
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'GET':
        # Return JSON response for AJAX filtering requests
        return JsonResponse({
            'success': True,
            'tasks': get_tasks_json(tasks),
            'current_status_filter': status_filter,
            'current_sort': sort_by,
            'has_tasks': tasks.exists()
        })
    
    return render(request, 'tasks/task_list.html', {
        'tasks': tasks, 
        'form': form,
        'current_status_filter': status_filter,
        'current_sort': sort_by
    })

def get_tasks_json(tasks):
    """Helper function to convert tasks queryset to JSON format"""
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description or '',
            'due_date': task.due_date.strftime('%b %d, %Y %I:%M %p'),
            'due_date_local': task.due_date.strftime('%Y-%m-%dT%H:%M'),
            'priority': task.priority,
            'status': task.status,
            'is_completed': task.is_completed
        })
    return tasks_data

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            # Create task but don't save yet
            task = form.save(commit=False)
            # Assign the task to the current user
            task.user = request.user
            task.save()
            
            # Check if this is an AJAX request
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return JSON response for AJAX requests
                return JsonResponse({
                    'success': True,
                    'task': {
                        'id': task.id,
                        'title': task.title,
                        'description': task.description or '',
                        'due_date': task.due_date.strftime('%b %d, %Y %I:%M %p'),
                        'due_date_local': task.due_date.strftime('%Y-%m-%dT%H:%M'),
                        'priority': task.priority,
                        'status': task.status,
                        'is_completed': task.is_completed
                    }
                })
            else:
                # Regular form submission - redirect
                params = {}
                if request.GET.get('status'):
                    params['status'] = request.GET.get('status')
                if request.GET.get('sort'):
                    params['sort'] = request.GET.get('sort')
                return redirect_with_params('task_list', params)
        else:
            # Form is invalid
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return JSON response with errors for AJAX requests
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
            else:
                # Regular form submission - render with errors
                sort_by = request.GET.get('sort', 'due_date')
                status_filter = request.GET.get('status', '')
                
                # Start with tasks for the current user
                tasks = Task.objects.filter(user=request.user)
                
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

@login_required
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        try:
            task.delete()
            
            # Check if this is an AJAX request
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return JSON response for AJAX requests
                return JsonResponse({
                    'success': True,
                    'message': 'Task deleted successfully'
                })
            else:
                # Regular form submission - redirect
                return redirect('task_list')
        except Exception as e:
            # Handle any errors during deletion
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return JSON response with error for AJAX requests
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to delete task. Please try again.'
                }, status=400)
            else:
                # Regular form submission - redirect with error (could be enhanced)
                return redirect('task_list')
    
    # GET request - show delete confirmation page (fallback for non-JS)
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
