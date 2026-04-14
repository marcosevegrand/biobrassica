from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import normalize_portuguese_nif, validate_portuguese_nif

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
    }))
    password2 = forms.CharField(label='Confirmar password', widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
    }))

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
            }),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_('As passwords não coincidem.'))

        if p2:
            user = self.instance
            user.email = self.cleaned_data.get('email', '')
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            validate_password(p2, user=user)

        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    nif = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
        }),
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'preferred_language', 'nif')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest',
            }),
        }

    def clean_nif(self):
        nif = normalize_portuguese_nif(self.cleaned_data.get('nif', ''))
        validate_portuguese_nif(nif)
        return nif
