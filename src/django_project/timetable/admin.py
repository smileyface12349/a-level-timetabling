from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext, gettext_lazy as _

from .models import User, Lesson, Group, Link, Subject

# Register your models here.


TITLE_CHOICES = [('', "It doesn't matter"),
                 ('mr', 'Mr'),
                 ('mrs', 'Mrs'),
                 ('miss', 'Miss'),
                 ('ms', 'Ms'),
                 ('dr', 'Dr')]
USER_TYPES = [('student', 'Student'),
              ('teacher', 'Teacher')]
YEAR_CHOICES = [(None, 'N/A'),
                ('L6', 'L6'),
                ('U6', 'U6')]


class CustomUserCreationForm(UserCreationForm):
    title = forms.ChoiceField(choices=TITLE_CHOICES, required=False)
    first_name = forms.CharField()
    last_name = forms.CharField()
    user_type = forms.ChoiceField(choices=USER_TYPES)
    email = forms.EmailField()
    year_group = forms.ChoiceField(choices=YEAR_CHOICES, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'user_type', 'year_group')


class CustomUserChangeForm(UserChangeForm):
    title = forms.ChoiceField(choices=TITLE_CHOICES, required=False)
    first_name = forms.CharField()
    last_name = forms.CharField()
    user_type = forms.ChoiceField(choices=USER_TYPES)
    email = forms.EmailField()
    year_group = forms.ChoiceField(choices=YEAR_CHOICES, required=False)

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'year_group')


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'title', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    fieldsets = (
        (_('Authentication'), {'fields': ('username', 'email', 'password')}),
        (_('Details'), {
            'fields': ('first_name', 'last_name', 'title', 'user_type', 'year_group'),
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(Lesson)
admin.site.register(Group)
admin.site.register(Link)
admin.site.register(Subject)
