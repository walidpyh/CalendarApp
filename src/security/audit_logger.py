import logging
import json
import os
from datetime import datetime
from flask import request, current_app

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Set up logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler('logs/audit.log')
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
audit_logger.addHandler(file_handler)

def log_auth_event(event_type, user_id=None, username=None, success=False, details=None):
    """
    Log authentication events (login, logout, registration, password change)
    
    :param event_type: Type of event (login, logout, register, password_change)
    :param user_id: User ID if available
    :param username: Username/email if available
    :param success: Whether the action was successful
    :param details: Additional details about the event
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "username": username,
        "success": success,
        "ip_address": request.remote_addr,
        "user_agent": request.user_agent.string if request.user_agent else "Unknown",
        "details": details or {}
    }
    
    audit_logger.info(json.dumps(log_data))

def log_data_event(event_type, user_id, resource_id=None, resource_type=None, action=None, details=None):
    """
    Log data modification events (create, update, delete)
    
    :param event_type: Type of event (create, update, delete)
    :param user_id: User ID performing the action
    :param resource_id: ID of the affected resource
    :param resource_type: Type of resource (event, user, etc.)
    :param action: Action performed
    :param details: Additional details about the event
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "resource_id": resource_id,
        "resource_type": resource_type,
        "action": action,
        "ip_address": request.remote_addr,
        "user_agent": request.user_agent.string if request.user_agent else "Unknown",
        "details": details or {}
    }
    
    audit_logger.info(json.dumps(log_data)) 