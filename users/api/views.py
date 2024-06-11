from rest_framework import generics
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
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from users.api.serializers import (
    UserSignUpSerializer,
    VerifyUserEmailSerializer,
)
# from django.utils.http import urlsafe_base64_decode
# from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
# from django.contrib.auth.tokens import PasswordResetTokenGenerator
# from django.utils import timezone
from users.utils import send_normal_email
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from users.models import (
    User,
    OneTimePassword,
)
import random
# from django.contrib.sites.shortcuts import get_current_site
# from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
# from rest_framework.pagination import CursorPagination
# from django.shortcuts import get_object_or_404
# from rest_framework.exceptions import ValidationError, ParseError
from django.template.loader import render_to_string
# from django.views.generic import TemplateView
# from users.permissions import IsHostUser, IsNormalUser
# import traceback
# from django.db.models import Q
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
                return Response(sr(code=201, message="OTP Resent to your Email"), status=RES_201)
            else:
                return Response({
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message_code': 'Failed',
                    'data': {
                        'message': 'Account Already Exists! Please login'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                return Response(sr(code=201, message="OTP Resent to your Email"), status=RES_201)

        except ObjectDoesNotExist:
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                otp = self.generate_otp()
                self.save_otp(user, otp, user.email)
                self.send_verification_email(user.email, user.first_name, otp)
                return Response({
                    'code': status.HTTP_201_CREATED,
                    'message_code': 'Success',
                    'data': {
                        "message": "OTP sent to your email"
                    },
                }, status=status.HTTP_201_CREATED)

        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message_code': 'Error',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

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
            'email_subject': "Thanks for SignUp On SociHubOut",
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
                return Response({
                    "code": status.HTTP_200_OK,
                    "message_code": "Success",
                    "data": {
                        'message': 'User Verified!'
                    }
                }, status=status.HTTP_200_OK)
        except OneTimePassword.DoesNotExist as e:
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message_code": "Failed",
                "data": {
                    'message': 'Invalid OTP!'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
