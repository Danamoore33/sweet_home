from functools import wraps
from flask_login import current_user
from flask import abort
from app.models import Permission

def permission_required(permission):
    def decorate(f):
        @wraps(f)
        def wrapper(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args,**kwargs)
        return wrapper
    return decorate

def admin_required(f):
    return permission_required(Permission.ADMIN)(f)