"""
Base serializer classes for the CDA unified backend.

All app serializers should extend BaseModelSerializer instead of
rest_framework.serializers.ModelSerializer. This ensures consistent
audit fields and response structure across all endpoints.
"""

from rest_framework import serializers
from core.middleware import get_current_user


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Extended ModelSerializer that:
    1. Auto-populates `created_by` from the request user (via middleware)
    2. Adds read-only display fields for audit trail
    3. Enforces a standard `_display` suffix convention for related objects

    Subclasses should set `Meta.model` and `Meta.fields` as usual.
    If the model has a `created_by` ForeignKey, it will be auto-set on create.
    """

    created_at = serializers.DateTimeField(read_only=True, required=False)
    updated_at = serializers.DateTimeField(read_only=True, required=False)
    created_by_display = serializers.SerializerMethodField(required=False)

    def get_created_by_display(self, obj):
        """Return the display name of the user who created this record."""
        created_by = getattr(obj, "created_by", None)
        if created_by is None:
            return None
        return created_by.get_full_name() or created_by.email

    def create(self, validated_data):
        """Auto-set `created_by` if the model has that field and it
        wasn't explicitly provided."""
        model = self.Meta.model
        if (
            hasattr(model, "created_by")
            and "created_by" not in validated_data
        ):
            user = get_current_user()
            if user and user.is_authenticated:
                validated_data["created_by"] = user
        return super().create(validated_data)

    class Meta:
        abstract = True
        # Subclasses should always include 'created_at', 'updated_at',
        # and 'created_by_display' in their fields if the model has
        # those columns. The base class declares them as serializer
        # fields so they just need to be listed in Meta.fields.


class ReadOnlyBaseSerializer(BaseModelSerializer):
    """
    Base serializer for read-only endpoints (list/retrieve).
    Disables create/update by default.
    """

    def create(self, validated_data):
        raise NotImplementedError("This serializer is read-only.")

    def update(self, instance, validated_data):
        raise NotImplementedError("This serializer is read-only.")
