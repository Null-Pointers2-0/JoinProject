from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
from web_app.models import *
from web_app.forms import *


def create_test_image(format='JPEG', extension='jpg'):
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return SimpleUploadedFile(
        f'test.{extension}',
        buffer.read(),
        content_type=f'image/{format.lower()}'
    )


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
            'terms_accepted': True,
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

class CustomUserChangeFormTest(TestCase):
    
    def test_succes_avatar(self):
        img = create_test_image(format='JPEG', extension='jpg')
        form = CustomUserChangeForm({
            'username': 'testuser',
        }, files={'avatar': img})
        self.assertTrue(form.is_valid())

    def test_valid_png_avatar(self):
        img = create_test_image(format='PNG', extension='png')
        form = CustomUserChangeForm({
            'username': 'testuser',
        }, files={'avatar': img})
        self.assertTrue(form.is_valid())

    def test_wrong_extension_avatar(self):
        img = create_test_image(format='PNG', extension='gif')
        form = CustomUserChangeForm({
            'username': 'testuser',
        }, files={'avatar': img})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['avatar'], ["Solo se permiten archivos JPG o PNG."])

    def test_wrong_file_type_avatar(self):
        txt_file = SimpleUploadedFile('file.txt', b'file_content', content_type='text/plain')
        form = CustomUserChangeForm({
            'username': 'testuser',
        }, files={'avatar': txt_file})
        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)

    def test_user_exists(self):
        img = create_test_image(format='JPEG', extension='jpg')
        form = CustomUserChangeForm({
            'username': 'testuser',
        }, files={'avatar': img})
        user = CustomUser.objects.create_user(username='testuser', password='password123', email='test@mail.com')
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['username'], ["Ya existe un usuario con este nombre."])
