from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, FamilyLink


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role")
    list_filter = ("role",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("CDA", {"fields": ("role", "preferred_name", "phone")}),
    )


@admin.register(FamilyLink)
class FamilyLinkAdmin(admin.ModelAdmin):
    list_display = ("parent", "student", "relationship")
