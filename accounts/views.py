import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignUpForm, ProfileUpdateForm, UserUpdateForm
from .models import EmailVerificationToken, Profile
from notifications.services import send_login_notification, send_welcome_email


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        # Fire login notification email asynchronously-safe
        try:
            send_login_notification(self.request.user, self.request)
        except Exception:
            pass
        return response


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        # Generate verification token
        token = secrets.token_urlsafe(32)
        EmailVerificationToken.objects.create(user=user, token=token)
        try:
            send_welcome_email(user, token)
        except Exception:
            pass
        messages.success(self.request, "Account created! Check your email to verify your account, then log in.")
        return response


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


class VerifyEmailView(View):
    def get(self, request, token):
        ev = get_object_or_404(EmailVerificationToken, token=token, used=False)
        ev.used = True
        ev.save()
        ev.user.profile.email_verified = True
        ev.user.profile.save(update_fields=['email_verified'])
        messages.success(request, "Email verified successfully. You can now log in.")
        return redirect('accounts:login')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
        return render(request, self.template_name, {'u_form': u_form, 'p_form': p_form})

    def post(self, request):
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Profile updated.")
            return redirect('accounts:profile')
        return render(request, self.template_name, {'u_form': u_form, 'p_form': p_form})


# Password reset views (templates provided)
class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
