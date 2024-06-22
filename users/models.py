from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from users.models_utils import encode_sha256_base32
import uuid


class UserManager(BaseUserManager):
    '''
    Custom User Manager
    '''

    def email_validator(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError(_("You must provide a valid email address"))

    def create_user(self, **kwargs):
        password = kwargs.pop('password')
        if not kwargs.get('email'):
            raise ValueError('Email is required.')
        kwargs['email'] = self.normalize_email(kwargs['email'])
        user = self.model(**kwargs)
        if password:
            user.set_password(password)
        else:
            raise ValueError(_("You must provide a valid email address"))
        user.referral_code = self.generate_referral_code(kwargs['email'])
        user.save(using=self._db)
        return user

    def create_superuser(self, *args, **kwargs):
        user = self.create_user(**kwargs)
        user.is_superuser = True
        user.is_staff = True
        user.status = User.Status.ACTIVATED
        user.save(using=self._db)
        return user

    def generate_referral_code(self, email=None):
        if email:
            referral_code = encode_sha256_base32(email)
        else:
            raise ValueError(_("You must provide a valid email address"))
        while User.objects.filter(referral_code=referral_code).exists():
            referral_code = encode_sha256_base32(str(uuid.uuid4()))
        return referral_code


class User(AbstractBaseUser, PermissionsMixin):
    '''
    Custom User Model
    '''
    class Role(models.IntegerChoices):
        HOST = 1, _('Host')  # Event Creater And Manager
        USER = 2, _('User')  # Normal User

    class Status(models.IntegerChoices):
        ACTIVATED = 1, _('Activated')
        DEACTIVATED = 2, _('Deactivated')

    first_name = models.CharField(_('First Name'), max_length=50)
    last_name = models.CharField(_('Last Name'), max_length=50)
    email = models.EmailField(_('Email Address'), unique=True, db_index=True)
    role = models.PositiveSmallIntegerField(_('Role'), choices=Role.choices)
    group_name = models.CharField(
        _('Group'), max_length=200, null=True, blank=True)
    is_verified = models.BooleanField(_('Is Verified'), default=False)
    is_staff = models.BooleanField(_('Is Staff'), default=False)
    is_app_user = models.BooleanField(_('Is App User'), default=False)
    is_admin_owner = models.BooleanField(_('Is Admin Owner'), default=False)
    status = models.PositiveSmallIntegerField(
        _('Activation Status'), default=Status.ACTIVATED, choices=Status.choices)
    is_new = models.BooleanField(_('New User'), default=True)
    referral_code = models.CharField(max_length=8, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    profile_image = models.URLField(_('Profile Picture'),blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    objects = UserManager()

    class Meta:
        ordering = ('pk',)

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name.title()} {self.last_name.title()}"


class OneTimePassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=8)
    email = models.EmailField(
        max_length=255, unique=True, default='example@example.com')

    def __str__(self):
        return f"{self.user.first_name} - {self.user.email} - {self.otp}"
