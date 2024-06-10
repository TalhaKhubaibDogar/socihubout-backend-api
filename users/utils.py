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
