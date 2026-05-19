from django import forms

INPUT_CLASS = 'form-input'


class RegisterForm(forms.Form):
    username = forms.CharField(
        label='Имя',
        max_length=100,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Александр'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'you@university.ru'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Минимум 8 символов'}),
    )
    password2 = forms.CharField(
        label='Повтор пароля',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Повторите пароль'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        from users.models import User

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже есть.')
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError('Пароли не совпадают.')
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'you@university.ru'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ваш пароль'}),
    )


class ProfileForm(forms.Form):
    username = forms.CharField(
        label='Имя',
        max_length=100,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS}),
    )
