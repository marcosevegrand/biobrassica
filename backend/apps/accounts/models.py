from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField('email', unique=True)
    phone = models.CharField('telefone', max_length=20, blank=True)
    preferred_language = models.CharField(
        'idioma preferido',
        max_length=2,
        choices=[('pt', 'Português'), ('en', 'Inglês'), ('fr', 'Francês')],
        default='pt',
    )
    nif = models.CharField('NIF', max_length=9, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'utilizador'
        verbose_name_plural = 'utilizadores'

    def __str__(self):
        return self.email


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='utilizador')
    name = models.CharField('nome', max_length=255)
    line1 = models.CharField('Morada', max_length=255)
    line2 = models.CharField('Morada (cont.)', max_length=255, blank=True)
    city = models.CharField('Cidade', max_length=100)
    postal_code = models.CharField('Código Postal', max_length=10)
    country = models.CharField('País', max_length=2, default='PT')
    is_default = models.BooleanField('morada predefinida', default=False)

    class Meta:
        verbose_name = 'morada'
        verbose_name_plural = 'moradas'

    def __str__(self):
        return f'{self.name} - {self.line1}, {self.city}'
