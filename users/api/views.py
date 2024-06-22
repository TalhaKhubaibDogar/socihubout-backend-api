from rest_framework.status import (
    HTTP_200_OK as RES_200,
    HTTP_201_CREATED as RES_201,
    HTTP_202_ACCEPTED as RES_202,
    HTTP_400_BAD_REQUEST as RES_400,
    HTTP_401_UNAUTHORIZED as RES_401,
    HTTP_403_FORBIDDEN as RES_403,
    HTTP_404_NOT_FOUND as RES_404,
    HTTP_500_INTERNAL_SERVER_ERROR as RES_500,
)
from common.messages import (
    OTP_SENT,
    OTP_RESENT,
    OTP_EMAIL_SUBJECT,
    USER_EXISTS,
    USER_VERIFIED,
    INVALID_OTP,
    CHECK_EMAIL_RESET_PASSWORD,
    NO_ACCOUNT_EXISTS,
    PASSWORD_RESET_SUCCESS,
    LOGIN_SUCCESS,
    LOGOUT_SUCCESS,
    PROFILE_DATA_RETRIVED,
    USER_DOES_NOT_EXISTS,
    USER_PROFILE_UPDATED_SUCCESS,
    USER_PREFERENCES_CREATED
)
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from users.api.serializers import (
    UserSignUpSerializer,
    VerifyUserEmailSerializer,
    PasswordResetRequestSerializer,
    SetNewPasswordSerializer,
    LoginUserSerializer,
    LogoutUserSerializer,
    UserProfileSerializer,
    UserPreferenceSerializer
)
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from users.utils import send_normal_email, upload_to_s3
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from users.models import (
    User,
    OneTimePassword,
)
import random
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
# from rest_framework.pagination import CursorPagination
# from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, ParseError
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from users.permissions import IsHostUser, IsNormalUser
import traceback
from django.db.models import Q
from common.utils import success_response_builder as sr
from common.utils import error_response_builder as er


class SignUpView(GenericAPIView):
    serializer_class = UserSignUpSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.is_verified:
                otp = self.generate_otp()
                self.save_otp(user, otp, user.email)
                self.send_verification_email(user.email, user.first_name, otp)
                return Response(sr(code=201, message=OTP_SENT), status=RES_201)
            else:
                return Response(er(code=400, message=USER_EXISTS), status=RES_400)

        except ObjectDoesNotExist:
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                otp = self.generate_otp()
                self.save_otp(user, otp, user.email)
                self.send_verification_email(user.email, user.first_name, otp)
                return Response(sr(code=200, message=OTP_RESENT), status=RES_200)
        return Response(er(message=serializer.errors))

    def generate_otp(self):
        return random.randint(100000, 999999)

    def save_otp(self, user, otp, email):
        OneTimePassword.objects.update_or_create(
            email=email,
            defaults={'otp': otp, 'user': user}
        )

    def send_verification_email(self, email, first_name, otp):
        context = {
            'first_name': first_name,
            'otp': otp,
        }
        html_content = render_to_string('signup_template.html', context)
        email_data = {
            'email_body': html_content,
            'email_subject': OTP_EMAIL_SUBJECT,
            'to_email': email,
        }
        send_normal_email(email_data)


class VerifyUserEmailView(GenericAPIView):
    serializer_class = VerifyUserEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        user_otp = validated_data.get('otp')
        user_email = validated_data.get('email')

        try:
            otp_obj = OneTimePassword.objects.get(
                otp=user_otp, email=user_email)
            user = otp_obj.user
            if not user.is_verified:
                user.is_verified = True
                user.save()
                return Response(sr(message=USER_VERIFIED), status=RES_200)
        except OneTimePassword.DoesNotExist as e:
            return Response(er(message=INVALID_OTP), status=RES_404)


class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(
                data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            return Response(sr(code=200, message=CHECK_EMAIL_RESET_PASSWORD), status=RES_200)
        except Exception as e:
            return Response(er(message=e.args[0]), status=RES_404)


class PasswordResetConfirmView(TemplateView):
    template_name = 'set_password.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Base_URL'] = settings.BASE_URL
        return context


class SetNewPasswordView(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                return Response(sr(message=PASSWORD_RESET_SUCCESS), status=RES_200)
            return Response(er(message=serializer.errors), status=RES_400)
        except ValidationError as e:
            return Response(er(message=e.args[0]), status=RES_400)


class SuccessResetPasswordView(TemplateView):
    template_name = 'success_password_reset.html'


class LoginUserView(GenericAPIView):
    serializer_class = LoginUserSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(
                data=request.data, context={'request': request})
            if serializer.is_valid():
                return Response(sr(message=LOGIN_SUCCESS, data=serializer.data), status=RES_200)
            return Response(er(message=serializer.errors), status=RES_400)
        except Exception as e:
            return Response(er(message=e.args[0]), status=RES_400)


class LogoutUserView(GenericAPIView):
    serializer_class = LogoutUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.update()
                return Response(sr(message=LOGOUT_SUCCESS), status=RES_200)
            return Response(er(message=serializer.errors), status=RES_400)
        except Exception as e:
            return Response(er(message=e.args[0]), status=RES_400)


class UserProfileView(GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def get(self, request, *args, **kwargs):

        user_instance = self.request.user
        if user_instance:
            serializer = self.get_serializer(user_instance)
            return Response(sr(message=PROFILE_DATA_RETRIVED, data=serializer.data), status=RES_200)
        return Response(er(message=USER_DOES_NOT_EXISTS), status=RES_400)

    def post(self, request, *args, **kwargs):
        try:
            email = self.request.user.email
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                try:
                    user_instance = User.objects.get(email=email)
                except User.DoesNotExist:
                    return Response(er(message=USER_DOES_NOT_EXISTS), status=RES_400)

                profile_image = request.data.get('profile_image')
                first_name = request.data.get('first_name')
                last_name = request.data.get('last_name')
                print("dat", first_name, last_name)
                if profile_image:
                    s3_upload_files = upload_to_s3(profile_image)
                    user_instance.s3_url_profile = s3_upload_files[0]
                    user_instance.profile_image = s3_upload_files[1]
                    user_instance.profile_cloudfront_url = s3_upload_files[1]

                if first_name:
                    user_instance.first_name = first_name
                if last_name:
                    user_instance.last_name = last_name
                user_instance.save()
                serializer = self.get_serializer(user_instance)
                return Response(sr(message=USER_PROFILE_UPDATED_SUCCESS, data=serializer.data), status=RES_200)
            return Response(er(message=serializer.errors), status=RES_400)
        except Exception as e:
            return Response(er(message=e.args[0]), status=RES_400)

class UserPreferenceView(generics.CreateAPIView):
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user_preferences = serializer.save()
                return Response(sr(message=USER_PREFERENCES_CREATED), status=RES_200)
            return Response(er(message=serializer.errors), status=RES_400)
        except Exception as e:
            return Response(er(message=e.args[0]), status=RES_400)