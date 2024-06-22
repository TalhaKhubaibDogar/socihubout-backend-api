from django.urls import path
from users.api.views import (
    SignUpView,
    VerifyUserEmailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    SetNewPasswordView,
    SuccessResetPasswordView,
    LoginUserView,
    LogoutUserView,
    UserProfileView,
    UserPreferenceView
)

app_name = 'users_api_v1'
urlpatterns = [
    path('signup/', SignUpView.as_view(), name='users-register'),
    path('verify-otp/', VerifyUserEmailView.as_view(), name='users-verifyotp'),
    path('password-reset/', PasswordResetRequestView.as_view(),
         name='reset-password'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(),
         name='password-reset-confirm'),
    path('set-new-password/', SetNewPasswordView.as_view(), name="set-new-password"),
    path('password-reset-success/', SuccessResetPasswordView.as_view(),
         name="success-reset-password"),
    path('login/', LoginUserView.as_view(), name="user-login"),
    path('logout/', LogoutUserView.as_view(), name="user-logout"),
    path('profile/', UserProfileView.as_view(), name="get-user-profile"),
    path('preference/', UserPreferenceView.as_view(), name="user-prefernce"),
]
