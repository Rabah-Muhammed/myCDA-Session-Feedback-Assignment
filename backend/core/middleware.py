"""
Request audit middleware.

Attaches the authenticated user to thread-local storage so that
model-layer code (e.g. BaseModelSerializer.create) can access the
current user without passing `request` through every layer.

Usage in serializers / models:
    from core.middleware import get_current_user
    user = get_current_user()
"""

import threading

_thread_locals = threading.local()


def get_current_user():
    """
    Return the authenticated user for the current thread.
    Checks the thread's live request object first so that users authenticated
    by Django REST Framework (TokenAuth) inside the view are resolved dynamically.
    Falls back to _thread_locals.user for standard session-based requests.
    """
    req = getattr(_thread_locals, "request", None)
    if req and hasattr(req, "user") and req.user.is_authenticated:
        return req.user
    return getattr(_thread_locals, "user", None)


class RequestAuditMiddleware:
    """
    Stores the request in thread-local storage for the duration of the request.
    Downstream code can call `get_current_user()` to retrieve the authenticated user.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store both request reference and initial user
        _thread_locals.request = request
        _thread_locals.user = getattr(request, "user", None)
        try:
            response = self.get_response(request)
        finally:
            # Clean up after the request to avoid leaking across threads
            _thread_locals.request = None
            _thread_locals.user = None
        return response
