# feedback/admin.py
#
# Register your model(s) here for the Django admin.

from django.contrib import admin
from .models import SessionFeedback

admin.site.register(SessionFeedback)