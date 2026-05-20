import re
from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError


RUSSIAN_DATE_RE = re.compile(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$')


class RussianDateField(forms.DateField):
    """Поле даты в формате дд.мм.гггг."""

    input_formats = ['%d.%m.%Y']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'widget',
            forms.TextInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'дд.мм.гггг',
                    'inputmode': 'numeric',
                    'autocomplete': 'off',
                }
            ),
        )
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, datetime):
            return value.date()
        text = str(value).strip()
        match = RUSSIAN_DATE_RE.match(text)
        if not match:
            raise ValidationError(
                'Введите дату в формате дд.мм.гггг, например 25.06.2026.',
                code='invalid',
            )
        day, month, year = (int(match.group(i)) for i in range(1, 4))
        try:
            return datetime(year, month, day).date()
        except ValueError:
            raise ValidationError(
                'Некорректная дата. Проверьте день, месяц и год.',
                code='invalid',
            )

    def prepare_value(self, value):
        if hasattr(value, 'strftime'):
            return value.strftime('%d.%m.%Y')
        return value
