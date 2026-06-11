from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator

from .models import CustomUser, API, UserType, Gender, AgeRange, Province, Municipality

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

    gender = forms.ChoiceField(
        choices=Gender.choices,
        label=_("Gender"),
        required=True,
    )

    age_range = forms.ChoiceField(
        choices=AgeRange.choices,
        label=_("Age Range"),
        required=True,
    )

    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        label=_("Province"),
        required=True,
    )
        

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2', 'platforms',
                  'gender', 'age_range', 'province', 'municipality')

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
    
    def clean(self):
        cleaned_data = super().clean()
        province = cleaned_data.get('province')
        municipality_id = self.data.get('municipality')

        if province and municipality_id:
            try:
                municipality = Municipality.objects.get(id=municipality_id, province=province)
                cleaned_data['municipality'] = municipality
            except Municipality.DoesNotExist:
                self.add_error('municipality', _("The selected municipality does not belong to the selected province."))
        elif province:
            self.add_error('municipality', _("You must select a municipality."))

        return cleaned_data


    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.gender = self.cleaned_data.get('gender')
        user.age_range = self.cleaned_data.get('age_range')
        user.municipality = self.cleaned_data.get('municipality')

        if commit:
            user.save()
        return user
    
class CustomUserChangeForm(UserChangeForm):
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        label=_("Province"),
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'avatar', 'bio',
            'type', 'gender', 'age_range', 'municipality',
        ]
        help_texts = {field: '' for field in fields}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.municipality:
            self.fields['province'].initial = self.instance.municipality.province
            self.fields['province'].widget.attrs['data-current-province'] = self.instance.municipality.province_id

    def clean(self):
        cleaned_data = super().clean()
        province = cleaned_data.get('province')
        municipality_id = self.data.get('municipality')

        if province and municipality_id:
            try:
                municipality = Municipality.objects.get(id=municipality_id, province=province)
                cleaned_data['municipality'] = municipality
            except Municipality.DoesNotExist:
                self.add_error('municipality', _("The selected municipality does not belong to the selected province."))
        elif province:
            self.add_error('municipality', _("You must select a municipality."))

        return cleaned_data

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

class CustomUserAdminCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "type", "subscriptions")