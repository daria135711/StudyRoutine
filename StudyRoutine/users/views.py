from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from users.auth_helpers import (
    check_user_password,
    get_current_user,
    hash_password,
    login_required,
    login_user,
    logout_user,
)
from users.forms import LoginForm, ProfileForm, RegisterForm
from users.models import User


def _redirect_after_auth(request):
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
    ):
        return redirect(next_url)
    return redirect('exams:dashboard')


def register(request):
    if get_current_user(request):
        return redirect('exams:dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create(
            username=form.cleaned_data['username'].strip(),
            email=form.cleaned_data['email'].strip().lower(),
            password=hash_password(form.cleaned_data['password']),
        )
        login_user(request, user)
        messages.success(request, 'Регистрация прошла успешно.')
        return _redirect_after_auth(request)

    return render(request, 'users/register.html', {'form': form})


def login(request):
    if get_current_user(request):
        return redirect('exams:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user is None or not check_user_password(user, form.cleaned_data['password']):
            messages.error(request, 'Неверный email или пароль.')
        else:
            login_user(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return _redirect_after_auth(request)

    return render(request, 'users/login.html', {'form': form, 'next': request.GET.get('next', '')})


def logout(request):
    logout_user(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('exams:main')


@login_required
def profile(request):
    user = get_current_user(request)
    form = ProfileForm(
        request.POST or None,
        initial={'username': user.username, 'email': user.email},
    )
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            messages.error(request, 'Этот email уже занят.')
        else:
            user.username = form.cleaned_data['username'].strip()
            user.email = email
            user.save(update_fields=['username', 'email'])
            messages.success(request, 'Профиль обновлён.')
            return redirect('users:profile')

    return render(request, 'users/profile.html', {'form': form, 'active_nav': 'profile'})
