from django.db import models


class Students(models.Model):
    first_name = models.CharField(max_length=16)
    last_name = models.CharField(max_length=16)
    username = models.CharField(max_length=32)
    password_hash = models.CharField(max_length=32)


class Subjects(models.Model):
    name = models.CharField(max_length=16)


class StudentSubjects(models.Model):
    student = models.ForeignKey(
        'Students',
        on_delete=models.CASCADE,
    )
    subject = models.ForeignKey(
        'Subjects',
        on_delete=models.CASCADE
    )
    group = models.ForeignKey(
        'Groups',
        on_delete=models.SET_NULL,
        null=True
    )


class Groups(models.Model):
    teacher = models.ForeignKey(
        'Teachers',
        on_delete=models.SET_NULL,
        null=True
    )


class Teachers(models.Model):
    first_name = models.CharField(max_length=16)
    last_name = models.CharField(max_length=16)
    title = models.CharField(max_length=8)
    username = models.CharField(max_length=32)
    password_hash = models.CharField(max_length=32)


class Lessons(models.Model):
    group = models.ForeignKey(
        'Groups',
        on_delete=models.CASCADE
    )
    duration = models.DurationField()
    topic = models.CharField(max_length=128)
    scheduled_datetime = models.DateTimeField()