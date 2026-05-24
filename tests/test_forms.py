from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
from web_app.models import CustomUser, API
from web_app.forms import CustomUserCreationForm, CustomUserChangeForm


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
        """Comprueba que contraseñas distintas invalidan el formulario."""
        form = CustomUserCreationForm({
            'username': 'testuser',
            'email': 'test@mail.com',
            'password': 'password123',
            'password2': 'password456',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['password2'], ["Las contraseñas no coinciden"])

    def test_password_matches(self):
        """Comprueba que contraseñas iguales permiten validar el formulario."""
        form = CustomUserCreationForm({
            'username': 'testuser',
            'email': 'test@mail.com',
            'password': 'password123',
            'password2': 'password123',
            'terms_accepted': True,
        })
        self.assertTrue(form.is_valid())

    def test_terms_not_accepted(self):
        """Comprueba que sin aceptar términos el formulario es inválido."""
        form = CustomUserCreationForm({
            'username': 'testuser',
            'email': 'test@mail.com',
            'password': 'password123',
            'password2': 'password123',
            'terms_accepted': False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('terms_accepted', form.errors)


class CustomUserChangeFormTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser', password='password123'
        )
    
    def test_succes_avatar(self):
        """Comprueba que un avatar JPG válido es aceptado."""
        img = create_test_image(format='JPEG', extension='jpg')
        form = CustomUserChangeForm(
            {'username': 'testuser', 'type': 'Consumer'},
            files={'avatar': img},
            instance=self.user
        )
        self.assertTrue(form.is_valid())

    def test_valid_png_avatar(self):
        """Comprueba que un avatar PNG válido es aceptado."""
        img = create_test_image(format='PNG', extension='png')
        form = CustomUserChangeForm(
            {'username': 'testuser', 'type': 'Consumer'},
            files={'avatar': img},
            instance=self.user
        )
        self.assertTrue(form.is_valid())

    def test_wrong_file_type_avatar(self):
        """Comprueba que un archivo de texto es rechazado como avatar."""
        txt_file = SimpleUploadedFile('file.txt', b'file_content', content_type='text/plain')
        form = CustomUserChangeForm(
            {'username': 'testuser', 'type': 'Consumer'},
            files={'avatar': txt_file},
            instance=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)

    def test_wrong_extension_avatar(self):
        """Comprueba que una imagen GIF con extensión .gif es rechazada."""
        img = create_test_image(format='PNG', extension='gif')
        form = CustomUserChangeForm(
            {'username': 'testuser', 'type': 'Consumer'},
            files={'avatar': img},
            instance=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['avatar'], ["Solo se permiten archivos JPG o PNG."])
