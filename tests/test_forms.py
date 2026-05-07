from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from web_app.models import *
from web_app.forms import *

class CustomUserCreationFormTest(TestCase):
    def test_password_does_not_match(self):
        form = CustomUserCreationForm({
            'username': 'testuser',
            'email': 'test@mail.com',
            'password': 'password123',
            'password2': 'password456',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['password2'], ["Las contraseñas no coinciden"])

    def test_password_matches(self):
        form = CustomUserCreationForm({
            'username': 'testuser',
            'email': 'test@mail.com',
            'password': 'password123',
            'password2': 'password123',
        })
        self.assertTrue(form.is_valid())

    def test_terms_not_accepted(self):
        form = CustomUserCreationForm({
            'username': 'testuser',
            'email': 'test@mail.com',
            'password': 'password123',
            'password2': 'password123',
            'terms_accepted': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['terms_accepted'], ["Debe aceptar los términos y condiciones para continuar."])
