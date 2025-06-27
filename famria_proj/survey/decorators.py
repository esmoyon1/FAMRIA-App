from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            user_role = request.user.profile.role
            if not user_role:
                messages.error(request, 'You do not have a role assigned. Please contact an administrator.')
                raise PermissionDenied
            
            if user_role.name not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                raise PermissionDenied
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    'admin': [
        'manage_users',
        'manage_surveys',
        'manage_questions',
        'manage_responses',
        'view_analytics',
        'export_data'
    ],
    'staff': [
        'manage_surveys',
        'manage_questions',
        'manage_responses',
        'view_analytics',
        'export_data'
    ],
    'enumerator': [
        'submit_response',
        'edit_response',
        'view_questions'
    ],
    'respondent': [
        'submit_response',
        'view_surveys'
    ]
}

def has_permission(user, permission):
    if not user.is_authenticated or not user.profile.role:
        return False
    return permission in ROLE_PERMISSIONS.get(user.profile.role.name, [])
