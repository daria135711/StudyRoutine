from django.contrib import messages
from django.shortcuts import redirect, render

from users.auth_helpers import (
    check_user_password,
    get_current_user,
    hash_password,
    login_user,
    logout_user,
)
from users.forms import LoginForm, RegisterForm
from users.models import User


def register(request):
    if get_current_user(request):
        return redirect('exams:home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create(
            username=form.cleaned_data['username'].strip(),
            email=form.cleaned_data['email'].strip().lower(),
            password=hash_password(form.cleaned_data['password']),
        )
        login_user(request, user)
        messages.success(request, 'Регистрация прошла успешно.')
        return redirect('exams:home')

    return render(request, 'users/register.html', {'form': form})


def login(request):
    if get_current_user(request):
        return redirect('exams:home')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user is None or not check_user_password(user, form.cleaned_data['password']):
            messages.error(request, 'Неверный email или пароль.')
        else:
            login_user(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('exams:home')

    return render(request, 'users/login.html', {'form': form})


def logout(request):
    logout_user(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('users:login')
