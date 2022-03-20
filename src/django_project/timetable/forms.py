from django.contrib.auth.forms import AuthenticationForm, UsernameField

from django import forms
from django.utils.safestring import mark_safe

from .fields import CustomModelChoiceField
from .models import Group, User


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


class ScheduleForm(forms.Form):

    def __init__(self, *args, **kwargs): # this is required to receive the request object
        self.request = kwargs.pop('request')
        # initialise the form
        super(ScheduleForm, self).__init__(*args, **kwargs)
        # modify the group field to include all the relevant groups
        self.fields['group'].queryset = Group.objects.filter(link__user_id__id__exact=self.request.user.id)

    group = CustomModelChoiceField(widget=forms.Select(
        attrs={
            'id': 'group-select'
        }),
        label='Class:', required=True,
        queryset=Group.objects.filter(link__user_id__id__exact=None),
        to_field_name='name', empty_label=None)
    topic = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'w-100 mb-2',
               'placeholder': 'What will the lesson be about? (optional)',
               'id': 'topic-input'}),
        label='', max_length=128, required=False)
    buttons_html = """
        <button type="button" onclick="document.getElementById('duration-input-number').value=40;" class="btn-secondary btn px-1 py-0">40</button>
        <button type="button" onclick="document.getElementById('duration-input-number').value=80;" class="btn-secondary btn px-1 py-0">80</button>
        <button type="button" onclick="document.getElementById('duration-input-number').value=100;" class="btn-secondary btn px-1 py-0">100</button>
        <button type="button" onclick="document.getElementById('duration-input-number').value=120;" class="btn-secondary btn px-1 py-0">120</button>
    """
    duration = forms.DurationField(widget=forms.NumberInput(
        attrs={
            'class': 'mb-2',
            'id': 'duration-input-number',
            'step': '5',
            'value': '60'
        }),
        label=mark_safe(f"Duration (minutes): {buttons_html}"))
