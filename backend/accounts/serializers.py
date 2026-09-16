from django.contrib.auth import authenticate
from rest_framework import serializers

from core.serializers import BaseModelSerializer
from .models import User, FamilyLink


class UserSerializer(BaseModelSerializer):
    display_name = serializers.CharField(
        source="get_display_name", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "preferred_name",
            "role",
            "display_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "role", "created_at", "updated_at"]


class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight user representation for nested use."""

    display_name = serializers.CharField(
        source="get_display_name", read_only=True
    )

    class Meta:
        model = User
        fields = ["id", "display_name", "role"]


class FamilyLinkSerializer(BaseModelSerializer):
    student_display = UserMinimalSerializer(source="student", read_only=True)

    class Meta:
        model = FamilyLink
        fields = [
            "id",
            "student",
            "student_display",
            "relationship",
            "created_at",
        ]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            username=data["username"], password=data["password"]
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        data["user"] = user
        return data
