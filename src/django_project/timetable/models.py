from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django_project import settings
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    title = models.CharField(max_length=8, default='')
    first_name = models.CharField(max_length=16)
    last_name = models.CharField(max_length=16)
    user_type = models.CharField(max_length=8, default='admin')


class Subject(models.Model):
    name = models.CharField(max_length=16)
    abbreviation = models.CharField(max_length=4)


class Link(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    subject_id = models.ForeignKey(
        'Subject',
        on_delete=models.CASCADE
    )
    group_id = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE
    )


class Group(models.Model):
    name = models.CharField(max_length=8)


class Lesson(models.Model):
    group = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE
    )
    duration = models.DurationField()
    topic = models.CharField(max_length=128)
    start = models.DateTimeField(null=True)
    fixed = models.BooleanField()
