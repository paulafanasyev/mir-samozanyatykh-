"""
Ownership check decorator for IDOR protection
"""

from functools import wraps
from fastapi import HTTPException


def require_ownership(model_class, user_field="user_id", admin_allowed=True):
    """
    Decorator to check resource ownership.

    Usage:
        @router.get("/{item_id}")
        @require_ownership(Item)
        async def get_item(item_id: int, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            resource_id = kwargs.get('id') or kwargs.get(f'{model_class.__tablename__}_id')

            if not current_user or not db:
                raise HTTPException(500, "Missing parameters for ownership check")

            resource = db.query(model_class).filter(model_class.id == resource_id).first()
            if not resource:
                raise HTTPException(404, "Not found")

            owner_id = getattr(resource, user_field)

            if owner_id != current_user.id:
                if admin_allowed and (current_user.is_admin or current_user.is_moderator):
                    pass
                else:
                    raise HTTPException(403, "Access denied")

            kwargs['resource'] = resource
            return await func(*args, **kwargs)
        return wrapper
    return decorator
