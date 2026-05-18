from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator

from .models import CustomUser, API, UserType

class CustomUserCreationForm(forms.ModelForm):
    """
    Handles the registration process for new users by capturing their credentials, 
    validating password confirmation, and ensuring they accept the mandatory terms of service.
    """
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

    platforms = forms.ModelMultipleChoiceField(
        queryset=API.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Select your platforms")
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2', 'platforms')

    def clean_password2(self):
        """
        Verifies that the initial password and the confirmation password match exactly 
        before allowing the user to proceed with the registration.
        """
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
        fields = ['username', 'first_name', 'last_name', 'email', 'avatar', 'bio', 'location', 'type']
        help_texts = {field: '' for field in fields}

    def clean_avatar(self):
        """
        Performs custom validation on the uploaded avatar file to strictly enforce 
        that users only submit images in standard JPG or PNG formats.
        """
        avatar = self.cleaned_data.get('avatar')

        if avatar:
            ext = avatar.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                raise ValidationError('Solo se permiten archivos JPG o PNG.')

        return avatar

class CustomUserAdminCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "type", "location")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'password1' in self.fields:
            del self.fields['password1']
        if 'password2' in self.fields:
            del self.fields['password2']
    
    def save(self, commit=True):
        """
        Sobrescribimos save para evitar que Django busque 'password1'.
        Simplemente creamos la instancia del modelo con los datos del form.
        """
        # No llamamos a super().save() porque ahí es donde explota el KeyError
        user = CustomUser(**self.cleaned_data)
        if commit:
            user.save()
        return user