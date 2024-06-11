from rest_framework.response import Response
from rest_framework import status
from users.utils import send_normal_email
from users.models import (
    User,
)

from rest_framework import serializers
# from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, ValidationError, ParseError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
# from django.utils.encoding import smart_str, force_str, smart_bytes
# from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
# from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import Exists, OuterRef
# from oauth2_provider.models import AccessToken, RefreshToken
# from users.utils import UserAccessToken
from django.utils import timezone
from common.utils import success_response_builder as sr
from common.utils import error_response_builder as er


class UserSignUpSerializer(serializers.ModelSerializer):
    role = serializers.IntegerField(required=True)
    password = serializers.CharField(
        write_only=True, min_length=8, max_length=68)
    password2 = serializers.CharField(
        write_only=True, min_length=8, max_length=68)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name',
                  'role', 'password', 'password2']

    def validate(self, attrs):
        password = attrs.get('password', '')
        password2 = attrs.get('password2', '')
        if password != password2:
            raise serializers.ValidationError("passwords do not match")
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=validated_data.get('password'),
            role=validated_data.get('role')
        )


class VerifyUserEmailSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6, required=True)
    email = serializers.EmailField(max_length=255, required=True)

    class Meta:
        fields = ["otp", "email"]

    def validate(self, attrs):
        extra_fields = set(self.initial_data.keys()) - set(self.fields.keys())
        try:
            if extra_fields:
                raise ParseError("Unknown Fields")
            return attrs
        except ParseError as e:
            raise ParseError({
                "code": status.HTTP_400_BAD_REQUEST,
                "message_code": "Failed",
                "data": {
                    "message": e.args[0]
                }
            })
