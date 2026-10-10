import random
import string
import threading

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.views import View
from django.views.generic import FormView, TemplateView

from users.forms import LoginForm, ForgetPasswordForm, ForgetPasswordEmailForm, AccountForm
from users.models import EmailVerification
from orders.utils import safe_next_url
from .utils import send_email_update_password

UserModel = get_user_model()


def generate_code():
    return ''.join(random.choices(string.digits, k=6))


# ──────────────────────────────────────────────
# Ro'yxatdan o'tish
# ──────────────────────────────────────────────
class RegisterView(View):
    template_name = "auth/user-register.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        username   = request.POST.get('username', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        errors = []

        if not first_name:
            errors.append("Ism kiritilmadi.")
        if not last_name:
            errors.append("Familiya kiritilmadi.")
        if not email:
            errors.append("Email kiritilmadi.")
        if not username:
            errors.append("Username kiritilmadi.")
        if not password1:
            errors.append("Parol kiritilmadi.")
        elif len(password1) < 8:
            errors.append("Parol kamida 8 ta belgidan iborat bo'lishi kerak.")
        if password1 and password2 and password1 != password2:
            errors.append("Parollar mos kelmadi.")
        if email and UserModel.objects.filter(email=email).exists():
            errors.append("Bu email allaqachon ro'yxatdan o'tgan.")
        if username and UserModel.objects.filter(username=username).exists():
            errors.append("Bu username allaqachon band.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, self.template_name, {'form_data': request.POST})

        # Foydalanuvchi yaratish (is_active=True — verifikatsiyasiz)
        try:
            with transaction.atomic():
                user = UserModel.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                )
        except IntegrityError:
            messages.error(
                request,
                "Bu username yoki email allaqachon ro'yxatdan o'tgan. Boshqasini tanlang."
            )
            return render(request, self.template_name, {'form_data': request.POST})

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Hisob muvaffaqiyatli yaratildi! Xush kelibsiz!")
        return redirect(safe_next_url(request, '/'))


# ──────────────────────────────────────────────
# Email OTP tasdiqlash
# ──────────────────────────────────────────────
class VerifyEmailView(View):
    template_name = "auth/email-verification-page.html"

    def get(self, request):
        user_id = request.session.get('verify_user_id')
        if not user_id:
            return redirect('users:register')
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return redirect('users:register')
        return render(request, self.template_name, {'email': user.email})

    def post(self, request):
        user_id = request.session.get('verify_user_id')
        if not user_id:
            return redirect('users:register')

        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return redirect('users:register')

        entered_code = request.POST.get('code', '').strip()

        if not entered_code:
            messages.error(request, "Kodni kiriting.")
            return render(request, self.template_name, {'email': user.email})

        try:
            verification = EmailVerification.objects.get(user=user)
        except EmailVerification.DoesNotExist:
            messages.error(request, "Tasdiqlash kodi topilmadi. Qayta ro'yxatdan o'ting.")
            return redirect('users:register')

        if timezone.now() > verification.expires_at:
            verification.delete()
            user.delete()
            messages.error(request, "Kod muddati o'tdi. Qayta ro'yxatdan o'ting.")
            return redirect('users:register')

        if entered_code != verification.code:
            verification.attempts += 1
            verification.save()
            if verification.attempts >= 5:
                verification.delete()
                user.delete()
                messages.error(request, "Ko'p marta noto'g'ri kod kiritildi. Qayta ro'yxatdan o'ting.")
                return redirect('users:register')
            messages.error(request, f"Noto'g'ri kod. {5 - verification.attempts} ta urinish qoldi.")
            return render(request, self.template_name, {'email': user.email})

        user.is_active = True
        user.save()
        verification.delete()
        del request.session['verify_user_id']

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Hisob muvaffaqiyatli yaratildi! Xush kelibsiz!")
        return redirect(safe_next_url(request, '/'))


# ──────────────────────────────────────────────
# Kodni qayta yuborish
# ──────────────────────────────────────────────
class ResendCodeView(View):
    def get(self, request):
        user_id = request.session.get('verify_user_id')
        if not user_id:
            return redirect('users:register')
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return redirect('users:register')

        code = generate_code()
        expires_at = timezone.now() + timedelta(minutes=10)
        EmailVerification.objects.filter(user=user).delete()
        EmailVerification.objects.create(user=user, code=code, expires_at=expires_at)

        try:
            send_mail(
                subject='Yangi tasdiqlash kodi',
                message=f'Yangi tasdiqlash kodingiz: {code}\n\nKod 10 daqiqa amal qiladi.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            messages.success(request, 'Yangi kod yuborildi.')
        except Exception as exc:
            messages.error(request, f'Email yuborishda xatolik: {exc}')

        return redirect('users:verify-email')


# ──────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────
class LoginFormView(FormView):
    template_name = "auth/user-login.html"
    form_class = LoginForm
    success_url = reverse_lazy("products:list")

    def form_valid(self, form):
        user = form.cleaned_data.get("user")
        login(request=self.request, user=user)
        messages.success(self.request, "Muvaffaqiyatli kirdingiz!")
        return redirect(safe_next_url(self.request, reverse_lazy("products:list")))

    def form_invalid(self, form):
        return super().form_invalid(form)


# ──────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────
class MyLogoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse_lazy('products:list'))

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse_lazy('products:list'))


# ──────────────────────────────────────────────
# Parolni unutdim
# ──────────────────────────────────────────────
class ForgetPasswordEmailTemplateView(TemplateView):
    template_name = "auth/email_confirmation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Parolni tiklash"
        context["header"] = "Email yuborildi"
        context["message"] = "Emailingizni tekshiring, parolni tiklash havolasi yuborildi."
        return context


class ForgetPasswordEmailView(FormView):
    template_name = "auth/forget-password-email.html"
    form_class = ForgetPasswordEmailForm
    success_url = reverse_lazy("users:forget-password-email")

    def form_valid(self, form):
        user = form.cleaned_data["user"]
        threading.Thread(target=send_email_update_password, args=(user, self.request)).start()
        return super().form_valid(form)


class UpdatePasswordFormView(FormView):
    template_name = 'auth/update-password.html'
    form_class = ForgetPasswordForm
    success_url = reverse_lazy("users:login")

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(get_user_model(), pk=self.kwargs.get("uid"))
        self.token = self.kwargs.get("token")
        if not default_token_generator.check_token(self.user, self.token):
            messages.error(request, "Havola muddati o'tgan yoki noto'g'ri.")
            return redirect(reverse_lazy("users:forget-password"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uid"] = self.kwargs.get("uid")
        context["token"] = self.token
        return context

    def form_valid(self, form):
        self.user.set_password(form.cleaned_data["new_password1"])
        self.user.save()
        messages.success(self.request, "Parolingiz muvaffaqiyatli yangilandi. Endi tizimga kiring.")
        return super().form_valid(form)


# ──────────────────────────────────────────────
# Profil
# ──────────────────────────────────────────────
class AccountView(LoginRequiredMixin, FormView):
    template_name = "auth/user-acount.html"
    form_class = AccountForm
    success_url = reverse_lazy("users:account")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Ma'lumotlaringiz saqlandi.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_obj"] = self.request.user
        return context