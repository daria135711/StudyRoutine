from functools import wraps
from urllib.parse import urlencode

from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import redirect
from django.urls import reverse

from users.models import User

SESSION_USER_KEY = 'study_user_id'


def get_current_user(request):
    user_id = request.session.get(SESSION_USER_KEY)
    if not user_id:
        return None
    return User.objects.filter(pk=user_id).first()


def login_user(request, user):
    request.session[SESSION_USER_KEY] = user.id_user


def logout_user(request):
    request.session.pop(SESSION_USER_KEY, None)


def hash_password(raw_password):
    return make_password(raw_password)


def check_user_password(user, raw_password):
    if not user.password:
        return False
    if user.password.startswith('pbkdf2_'):
        return check_password(raw_password, user.password)
    return user.password == raw_password


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if get_current_user(request) is None:
            login_url = reverse('users:login')
            next_url = request.get_full_path()
            return redirect(f'{login_url}?{urlencode({"next": next_url})}')
        return view_func(request, *args, **kwargs)

    return wrapper
