from django.contrib.auth import views as auth_views
from django.urls import path

from apps.auth.views.view_auth import RegisterUserView, LoginUserView, LogoutUserView, PasswordResetRequestView, \
  CustomPasswordResetConfirmView
from apps.auth.views.view_profile import ViewProfileView, UpdateProfileView

app_name = 'auth'

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
    path('profile/', ViewProfileView.as_view(), name='view_profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update_profile'),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset-confirm/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view(template_name="auth/reset_password/password_reset_complete.html"), name="password_reset_complete"),
]
