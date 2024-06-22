from rest_framework.response import Response
from rest_framework import status
from users.utils import send_normal_email
from users.models import (
    User,
)
from common.messages import (
    PASSWORDS_DO_NOT_MATCH,
    UNKNOWN_FIELDS,
    REVERSE_URL_NOT_FOUND,
    NO_ACCOUNT_EXISTS,
    UNAUTHENTICATED_TOKEN_ERROR, 
    INVALID_EMAIL, 
    INVALID_PASSWORD, 
    EMAIL_NOT_VERIFIED,
    INVALID_TOKEN,
    ACCESS_TOKEN_NOT_SET,
    BODY_CANNOT_BE_EMPTY
)

from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, ValidationError, ParseError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import Exists, OuterRef
from oauth2_provider.models import AccessToken, RefreshToken
from users.utils import UserAccessToken
from django.utils import timezone
from common.utils import success_response_builder as sr
from common.utils import error_response_builder as er
from django.urls import NoReverseMatch


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
            raise serializers.ValidationError(PASSWORDS_DO_NOT_MATCH)
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
        if extra_fields:
            raise serializers.ValidationError(UNKNOWN_FIELDS)
        return attrs

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, required=True)

    class Meta:
        fields = ['email']

    def validate(self, attrs):
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            request = self.context.get('request')
            current_site = get_current_site(request).domain
            try:
                relative_link = reverse(
                    'users_api_v1:password-reset-confirm',
                    kwargs={'uidb64': uidb64, 'token': token}
                )
            except NoReverseMatch:
                raise serializers.ValidationError(REVERSE_URL_NOT_FOUND)
            
            abslink = f'http://{current_site}{relative_link}'
            print(abslink)
            context = {
                'abs_link': abslink
            }
            html_content = render_to_string('reset_password.html', context)
            data = {
                'email_body': html_content,
                'email_subject': 'Reset Password SociHubOut',
                'to_email': user.email,
            }
            send_normal_email(data)
        else:
            raise serializers.ValidationError(NO_ACCOUNT_EXISTS)
        return super().validate(attrs)


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=8, max_length=68, write_only=True)
    confirmPassword = serializers.CharField(
        min_length=8, max_length=68, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)
    token = serializers.CharField(min_length=3, write_only=True)

    class Meta:
        fields = ['password', 'confirmPassword', 'uidb64', 'token']

    def validate(self, attrs):
        print("attrs", attrs)
        token = attrs.get('token')
        uidb64 = attrs.get('uidb64')
        password = attrs.get('password')
        confirmPassword = attrs.get('confirmPassword')
        userId = smart_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=userId)
        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError(UNAUTHENTICATED_TOKEN_ERROR)
        if password != confirmPassword:
            raise serializers.ValidationError(PASSWORDS_DO_NOT_MATCH)
        user.set_password(password)
        user.save()
        return user

class LoginUserSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(max_length=155, min_length=8)
    password = serializers.CharField(max_length=68, write_only=True)
    full_name = serializers.CharField(max_length=255, read_only=True)
    access_token = serializers.CharField(max_length=2000, read_only=True)
    refresh_token = serializers.CharField(max_length=2000, read_only=True)
    expire_on = serializers.CharField(read_only=True)
    is_new = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'is_new',
                  'password', 'full_name', 'role', 'access_token', 'refresh_token', 'expire_on', 'referral_code']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request = self.context.get('request')
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError(INVALID_EMAIL)
        user_data = authenticate(request, email=email, password=password)
        if not user_data:
            raise serializers.ValidationError(INVALID_PASSWORD)
        if not user_data.is_verified:
            raise serializers.ValidationError(EMAIL_NOT_VERIFIED)
        user_info = User.objects.get(email=email)
        is_new_user = user_info.is_new
        if user_info.is_new == True:
            user_info.is_new = False
            user_info.save()
        referral_code = user_info.referral_code
        if user_info.role == 1:
            referral_code = None
        user_access_token = UserAccessToken(request, user_info)
        tokens = user_access_token.create_oauth_token()
        return {
            'id': user_info.id,
            'email': user_data.email,
            'full_name': user_data.get_full_name,
            'first_name': user_info.first_name,
            'last_name': user_info.last_name,
            'is_new': is_new_user,
            'role': user_info.role,
            'referral_code': referral_code,
            'access_token': tokens["access_token"].token,
            'refresh_token': tokens["refresh_token"].token,
            'expire_on': tokens["access_token"].expires
        }


class LogoutUserSerializer(serializers.Serializer):
    token = serializers.CharField()

    class Meta:
        model = AccessToken
        fields = ('token', )
        extra_kwargs = {
            'token': {
                'write_only': True,
            }
        }

    def validate(self, attrs):
        token = attrs.get('token')
        try:
            self.instance = AccessToken.objects.get(token=token)
        except AccessToken.DoesNotExist:
            raise serializers.ValidationError(ACCESS_TOKEN_NOT_SET)
        return attrs

    def update(self, *args, **kwargs):
        if self.instance:
            self.instance.expires = timezone.now()
            self.instance.save()
            RefreshToken.objects.filter(
                access_token=self.instance.id).update(revoked=timezone.now())
            return self.instance
        raise serializers.ValidationError(ACCESS_TOKEN_NOT_SET)

class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'profile_image')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.profile_image:
            ret['profile_image'] = instance.profile_cloudfront_url  # or s3_url_profile
        return ret

    def validate(self, attrs):
        extra_fields = set(self.initial_data.keys()) - \
            set(self.fields.keys())
        if extra_fields:
            raise serializers.ValidationError(UNKNOWN_FIELDS)
        if not attrs:
            raise serializers.ValidationError(BODY_CANNOT_BE_EMPTY)
        return attrs
