import logging
from django.conf import settings

def log_error(message):
    """
    Log an error message to the centralized app.log file.
    
    Args:
        message (str): The error message to log
        
    Example:
        log_error("User authentication failed for user_id: 123")
        # Output: [2025-07-13 21:00:01] ERROR - tasks: User authentication failed for user_id: 123
    """
    logger = logging.getLogger('tasks')
    logger.error(message) 