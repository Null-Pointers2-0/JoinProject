from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator

from .models import *

class CustomUserCreationForm(forms.ModelForm):
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        help_text=''
    )
    email = forms.EmailField(
        label='Correo electrónico',
        required=True,
        help_text=''
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text=''
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput,
        help_text=''
    )

    terms_accepted = forms.BooleanField(
        required=True,
        label=_("I accept the terms and conditions of use"),
        error_messages={'required': _('You must accept the terms and conditions to continue.')}
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2')

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password is not None and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
    
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'avatar', 'bio', 'location']
        help_texts = {field: '' for field in fields}

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')

        if avatar:
            ext = avatar.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                raise ValidationError('Solo se permiten archivos JPG o PNG.')

        return avatar