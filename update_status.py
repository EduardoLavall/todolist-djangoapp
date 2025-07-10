#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_project.settings')
django.setup()

from tasks.models import Task

def update_not_started_to_ongoing():
    """Update all tasks with 'not_started' status to 'ongoing' status"""
    
    # Find all tasks with 'not_started' status
    not_started_tasks = Task.objects.filter(status='not_started')
    
    print(f"Found {not_started_tasks.count()} tasks with 'not_started' status")
    
    if not_started_tasks.count() > 0:
        # Update all these tasks to 'ongoing' status
        updated_count = not_started_tasks.update(status='ongoing')
        print(f"Successfully updated {updated_count} tasks to 'ongoing' status")
    else:
        print("No tasks with 'not_started' status found")
    
    # Show current status distribution
    print("\nCurrent task status distribution:")
    for status in Task.objects.values('status').distinct():
        count = Task.objects.filter(status=status['status']).count()
        print(f"  {status['status']}: {count} tasks")

if __name__ == '__main__':
    update_not_started_to_ongoing() 