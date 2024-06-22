import os
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError
import boto3
from django.core.mail import EmailMessage, send_mail
import random
from django.conf import settings
from users.models import User, OneTimePassword
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from datetime import date, datetime, timedelta
from django.utils import timezone
from oauthlib.oauth2.rfc6749.tokens import random_token_generator
from oauth2_provider.models import AccessToken, RefreshToken


def send_normal_email(data):
    email = EmailMessage(
        subject=data['email_subject'],
        body=data['email_body'],
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[data['to_email']]
    )
    email.content_subtype = 'html'
    email.send()

class UserAccessToken(object):
    ''' UserAccessToken '''

    def __init__(self, request, user):
        self.request = request
        self.user = user

    def create_oauth_token(self):
        '''
        Create Outh token by user_id and application name
        '''
        scopes = 'read write'
        expires = timezone.now() + timezone.timedelta(hours=settings.USER_TOKEN_EXPIRES)
        access_token = AccessToken.objects.create(
            user=self.user,
            token=random_token_generator(self.request),
            expires=expires,
            scope=scopes)

        refresh_token = RefreshToken.objects.create(
            user=self.user,
            token=random_token_generator(self.request),
            access_token=access_token,
            revoked=timezone.now() + timezone.timedelta(minutes=settings.REFRESH_TOKEN_EXPIRES)
        )
        tokens = dict()
        tokens['access_token'] = access_token
        tokens['refresh_token'] = refresh_token
        return tokens

    def revoke_oauth_tokens(self):
        '''
        revoke existing auth tokens so that user is logged out from existing sessions first
        '''
        RefreshToken.objects.filter(
            user=self.user).update(revoked=timezone.now())
        AccessToken.objects.filter(
            user=self.user).update(expires=timezone.now())