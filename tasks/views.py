from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Case, When, IntegerField, Value, Q
from django.http import JsonResponse
from django.contrib import messages
from .models import Task, TaskList
from .forms import TaskForm, UserRegistrationForm, TaskListForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .utils import log_error
import json
import re
import os
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, FileResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.utils.html import escape

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
def create_tasklist(request):
    if request.method == 'POST':
        form = TaskListForm(request.POST)
        if form.is_valid():
            tasklist = form.save(commit=False)
            tasklist.user = request.user
            try:
                tasklist.save()
                messages.success(request, f'📝 Task list "{tasklist.name}" created successfully!')
                return redirect('task_list')
            except:
                form.add_error('name', 'A task list with this name already exists.')
    else:
        form = TaskListForm()
    
    return render(request, 'tasks/create_tasklist.html', {'form': form})

@login_required
def task_list(request):
    user = request.user
    # Show TaskLists owned by or shared with the user
    user_tasklists = TaskList.objects.filter(Q(user=user) | Q(shared_with=user)).distinct().order_by('created_at')
    tasklist_id = request.GET.get('list')
    current_tasklist = None
    tasks = Task.objects.none()
    no_lists = False

    # Handle POST requests (toggle_completion, edit_task, etc.)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_completion':
            # Handle task completion toggle
            task_id = request.POST.get('task_id')
            is_completed = request.POST.get('is_completed') == '1'
            
            if task_id:
                try:
                    # Secure task access - ensure user owns the task
                    task = get_object_or_404(Task, id=task_id, user=user)
                    
                    # Toggle the task status based on completion
                    if is_completed:
                        task.status = Task.COMPLETED
                    else:
                        task.status = Task.ONGOING
                    
                    task.save()  # This will also update is_completed via the model's save method
                    
                    # Check if this is an AJAX request
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'status': task.status,
                            'is_completed': task.is_completed
                        })
                    else:
                        # Regular form submission - redirect back to task list
                        return redirect('task_list')
                        
                except Exception as e:
                    # Log the error using our centralized logging utility
                    log_error(f"Task status update failed for user {user.id}, task {task_id}: {str(e)}")
                    
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to update task status. Please try again.'
                        }, status=400)
                    else:
                        messages.error(request, 'Failed to update task status. Please try again.')
                        return redirect('task_list')
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid task ID.'
                    }, status=400)
                else:
                    messages.error(request, 'Invalid task ID.')
                    return redirect('task_list')
        
        elif action == 'edit_task':
            # Handle task editing (if needed for future)
            task_id = request.POST.get('task_id')
            if task_id:
                task = get_object_or_404(Task, id=task_id, user=user)
                form = TaskForm(request.POST, instance=task, user=user)
                if form.is_valid():
                    # Extra validation: ensure the selected TaskList belongs to the user
                    tasklist = form.cleaned_data['tasklist']
                    if not (tasklist.user == user or tasklist.shared_with.filter(id=user.id).exists()):
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'errors': {'tasklist': ['Invalid task list.']}
                            }, status=403)
                        else:
                            messages.error(request, 'Invalid task list.')
                            return redirect('task_list')
                    
                    form.save()
                    
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
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
                                'is_completed': task.is_completed,
                                'tasklist': task.tasklist.name,
                                'tasklist_id': task.tasklist.id
                            }
                        })
                    else:
                        return redirect('task_list')
                else:
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'errors': form.errors
                        })
                    else:
                        # For regular form submission, we'll need to handle this differently
                        # For now, redirect with error
                        messages.error(request, 'Please correct the errors below.')
                        return redirect('task_list')

    # GET request logic (existing code)
    if user_tasklists.exists():
        if tasklist_id:
            # Secure TaskList access: owner or shared_with
            current_tasklist = get_object_or_404(TaskList, Q(id=tasklist_id) & (Q(user=user) | Q(shared_with=user)))
        else:
            current_tasklist = user_tasklists.first()
        if current_tasklist:
            # Show tasks only if their TaskList is owned by or shared with the user
            tasks = Task.objects.filter(tasklist=current_tasklist)
    else:
        no_lists = True

    # Filtering and sorting (if needed)
    status_filter = request.GET.get('status', 'ongoing')
    sort_by = request.GET.get('sort', 'due_date')
    if not no_lists and current_tasklist:
        if status_filter == 'completed':
            tasks = tasks.filter(status='completed')
        elif status_filter == 'ongoing':
            tasks = tasks.filter(status='ongoing')
        # 'all' shows all tasks in the list
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

    # AJAX support for filtering
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        tasks_data = get_tasks_json(tasks)
        return JsonResponse({
            'success': True,
            'tasks': tasks_data,
            'has_tasks': bool(tasks_data)
        })

    form = TaskForm(user=user)
    context = {
        'tasks': tasks,
        'form': form,
        'user_tasklists': user_tasklists,
        'current_tasklist': current_tasklist,
        'no_lists': no_lists,
        'current_status_filter': status_filter,
        'current_sort': sort_by,
    }
    if 'list_error' in locals():
        context['list_error'] = list_error
    return render(request, 'tasks/task_list.html', context)

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
            'is_completed': task.is_completed,
            'tasklist': task.tasklist.name,
            'tasklist_id': task.tasklist.id
        })
    return tasks_data

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(user=request.user, data=request.POST)
        if form.is_valid():
            # Extra validation: ensure the selected TaskList belongs to the user or is shared
            tasklist = form.cleaned_data['tasklist']
            user = request.user
            if not (tasklist.user == user or tasklist.shared_with.filter(id=user.id).exists()):
                return JsonResponse({'success': False, 'errors': {'tasklist': ['Invalid task list.']}}, status=403) if request.headers.get('x-requested-with') == 'XMLHttpRequest' else redirect('task_list')
            # Create task but don't save yet
            task = form.save(commit=False)
            # Assign the task to the current user (creator)
            task.user = user
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
                        'is_completed': task.is_completed,
                        'tasklist': task.tasklist.name,
                        'tasklist_id': task.tasklist.id
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
                # Start with tasks for the current user (owned or shared)
                user = request.user
                user_tasklists = TaskList.objects.filter(Q(user=user) | Q(shared_with=user)).distinct()
                tasks = Task.objects.filter(tasklist__in=user_tasklists)
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
    # Secure Task access: only if user owns or is shared on the TaskList
    task = get_object_or_404(Task, pk=pk, tasklist__in=TaskList.objects.filter(Q(user=request.user) | Q(shared_with=request.user)).distinct())
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

@login_required
@require_POST
def share_tasklist(request):
    data = request.POST
    username = data.get('username', '').strip()
    tasklist_id = request.POST.get('tasklist_id') or request.GET.get('tasklist_id') or request.POST.get('list') or request.GET.get('list')
    # Try to get the TaskList ID from the referer if not present
    if not tasklist_id:
        referer = request.META.get('HTTP_REFERER', '')
        m = re.search(r'[?&]list=(\d+)', referer)
        if m:
            tasklist_id = m.group(1)
    if not tasklist_id:
        return JsonResponse({'success': False, 'message': 'TaskList not specified.'}, status=400)
    # Validate TaskList ownership
    try:
        tasklist = TaskList.objects.get(id=tasklist_id, user=request.user)
    except TaskList.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'You do not have permission to share this list.'}, status=403)
    # Validate username
    if not username:
        return JsonResponse({'success': False, 'message': 'Username is required.'}, status=400)
    try:
        target_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)
    # Prevent sharing with self
    if target_user == request.user:
        return JsonResponse({'success': False, 'message': 'You cannot share a list with yourself.'}, status=400)
    # Prevent duplicate sharing
    if tasklist.shared_with.filter(id=target_user.id).exists():
        return JsonResponse({'success': False, 'message': 'This user already has access to the list.'}, status=400)
    # Add user to shared_with
    tasklist.shared_with.add(target_user)
    return JsonResponse({'success': True, 'message': f'List shared with {target_user.username}.'})

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

import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def log_error_view(request):
    """
    Receive error log data from frontend and write to centralized log file.
    
    Expected JSON payload:
    {
        "message": "Error description",
        "severity": "ERROR",
        "source": "task_creation",
        "url": "http://localhost:8000/",
        "user_agent": "Mozilla/5.0...",
        "timestamp": "2025-07-13T20:45:00.000Z"
    }
    """
    try:
        # Parse JSON payload
        data = json.loads(request.body)
        
        # Validate required fields
        if 'message' not in data or not data['message']:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing or empty message field'
            }, status=400)
        
        # Extract and validate fields
        message = data['message'].strip()
        severity = data.get('severity', 'ERROR')
        source = data.get('source', 'frontend')
        url = data.get('url', 'unknown')
        user_agent = data.get('user_agent', 'unknown')
        timestamp = data.get('timestamp', 'unknown')
        
        # Create meaningful log message
        log_message = f"[{source}] {message} | URL: {url} | User-Agent: {user_agent} | Timestamp: {timestamp}"
        
        # Log the error using our utility function
        log_error(log_message)
        
        return JsonResponse({'status': 'ok'})
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        # Log the error in logging the error (meta-error)
        log_error(f"Error in log_error_view: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)

LOG_PATH = os.path.join(settings.BASE_DIR, 'app.log')

@login_required
def view_log_file(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("403 Forbidden: Staff access only.")
    if not os.path.exists(LOG_PATH):
        return render(request, 'tasks/logs.html', {'log_content': '', 'no_log': True, 'truncated': False})
    file_size = os.path.getsize(LOG_PATH)
    truncated = False
    log_content = ''
    if file_size > 1024 * 1024:  # >1MB
        # Tail last 500 lines
        with open(LOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            log_content = ''.join(lines[-500:])
            truncated = True
    else:
        with open(LOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            log_content = f.read()
    return render(request, 'tasks/logs.html', {
        'log_content': log_content,
        'no_log': False,
        'truncated': truncated
    })

@login_required
def download_log_file(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("403 Forbidden: Staff access only.")
    if not os.path.exists(LOG_PATH):
        return JsonResponse({'error': 'File not found'}, status=404)
    response = FileResponse(open(LOG_PATH, 'rb'), as_attachment=True, filename='app.log')
    return response
