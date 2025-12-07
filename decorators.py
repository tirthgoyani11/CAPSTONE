from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Admins can access everything, otherwise check specific role
            if current_user.role != 'admin' and current_user.role != required_role:
                # Flash message or just abort
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('core.dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
