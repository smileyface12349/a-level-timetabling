from django.contrib.auth.forms import AuthenticationForm, UsernameField

from django import forms
from django.utils.safestring import mark_safe

from .fields import CustomModelChoiceField
from .models import Group, User


class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'mb-3',
               'placeholder': '',
               'id': 'username-input'}),
        label='Username')
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'mb-2',
            'placeholder': '',
            'id': 'password-input',
        }),
        label='Password')


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
    buttons_html = ''
    durations = ['40', '80', '100', '120']
    for duration in durations:
        buttons_html += f'<button type="button" onclick="document.getElementById(\'duration-input-number\').value={duration};" class="btn-secondary btn px-1 py-0">{duration}</button>'
    duration = forms.DurationField(widget=forms.NumberInput(
        attrs={
            'class': 'mb-2',
            'id': 'duration-input-number',
            'step': '5',
            'value': '60'
        }),
        label=mark_safe(f"Duration (minutes): {buttons_html}"))
