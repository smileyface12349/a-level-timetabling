from django.db import models
from django.contrib.auth.models import AbstractUser
from django_project import settings


class User(AbstractUser):
    title = models.CharField(max_length=8)


class Subject(models.Model):
    name = models.CharField(max_length=16)


class StudentSubject(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.CASCADE
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        null=True
    )


class Group(models.Model):
    teacher = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True
    )


class Lesson(models.Model):
    group = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE
    )
    duration = models.DurationField()
    topic = models.CharField(max_length=128)
    scheduled_datetime = models.DateTimeField()