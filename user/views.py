from django.contrib.auth import get_user_model
from sesame.utils import get_query_string
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache
from oauth2_provider.models import AccessToken, RefreshToken, Application
from datetime import timedelta
import datetime
import secrets
import json
import jwt
from rest_framework import serializers
from oauthlib import common


def generate_token(user, secret_key):
    payload = {
        "user_id": user.pk,
        "username": user.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
    }

    return jwt.encode(payload, secret_key, "HS256")


class AccessTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires = serializers.DateTimeField()
    scope = serializers.CharField()
    user = serializers.CharField()
    application = serializers.CharField()


class RefreshTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    access_token = serializers.CharField()
    user = serializers.CharField()
    application = serializers.CharField()


class TestView(APIView):
    def get(self, request):
        User = get_user_model()
        user = User.objects.first()
        LOGIN_URL = "http://127.0.0.1:8000/sesame/login/"
        LOGIN_URL += get_query_string(user)
        return Response({"url": LOGIN_URL})


class MagicLinkTokenGeneration(APIView):
    def post(self):
        email = self.request.POST["email"]
        if email:
            token = secrets.token_urlsafe(nbytes=32)
            link = f"http://localhost:8000/magic-link/{token}"
            cache.set(token, email, timeout=10 * 60)
        return Response({"link": link})


class MagicLinkAuthentication(APIView):
    def get(self, request, token):
        email = cache.get(token)
        if email is None:
            return Response({"message": "email is not found"})
        cache.delete(token)
        User = get_user_model()
        if User.objects.filter(email=email).exists:
            user = User.objects.get(email=email)
            application = Application.objects.get(
                client_id="F9ZeHDSfihtFgNz4ZoHI4vQR3Qc3vYh6zBWx5CeH"
            )
            # Calculate the expiration time for the access token (e.g., 1 hour from now)
            expires = datetime.datetime.now() + timedelta(hours=1)

            access_token = AccessToken.objects.create(
                token=generate_token(user, common.generate_token()),
                user=user,
                application=application,
                scope="read write",  # Replace with your desired scope
                expires=expires,
            )
            # Create a refresh token for the access token
            refresh_token = RefreshToken.objects.create(
                token=generate_token(user, common.generate_token()),
                user=user,
                application=application,
                access_token=access_token,
            )
            access_token_data = AccessTokenSerializer(access_token).data
            refresh_token_data = RefreshTokenSerializer(refresh_token).data

            return Response(
                {
                    "access_token": access_token.token,
                    # 'expires_in': oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
                    "token_type": "Bearer",
                    "scope": access_token.scope,
                    "refresh_token": refresh_token.token,
                }
            )


# TODO make sure to run celery task to deleted the expired tokens to avoid unwanted use of data storage
