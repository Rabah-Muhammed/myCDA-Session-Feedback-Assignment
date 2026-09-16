from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FamilyLink
from .serializers import (
    FamilyLinkSerializer,
    LoginSerializer,
    UserSerializer,
)


class LoginView(APIView):
    """POST username + password, receive a token and user profile."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ProfileView(APIView):
    """GET the current user's profile and family links (if parent)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UserSerializer(request.user).data

        if request.user.role == "parent":
            links = FamilyLink.objects.filter(
                parent=request.user
            ).select_related("student")
            data["family_links"] = FamilyLinkSerializer(
                links, many=True
            ).data

        return Response(data)
