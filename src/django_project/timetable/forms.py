from django.contrib.auth.forms import AuthenticationForm, UsernameField

from django import forms


class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'w-100 mb-3',
               'placeholder': 'Username',
               'id': 'username'}),
        label='')
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'w-100 mb-2',
            'placeholder': 'Password',
            'id': 'password',
        }),
        label='')
