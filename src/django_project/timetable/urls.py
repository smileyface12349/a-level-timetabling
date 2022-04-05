from django.urls import path
from django.contrib.auth import views as django_views
from . import views
from .forms import LoginForm

urlpatterns = [
    path('test/', views.test),
    path('convert_tz/', views.convert_tz),

    path('login/', django_views.LoginView.as_view(template_name='timetable/login.html', authentication_form=LoginForm), name='timetable-login'),
    path('logout/', django_views.LogoutView.as_view(template_name='timetable/logout.html'), name='timetable-logout'),

    path('', views.login_redirect, name='timetable-login-redirect'),

    path('student/', views.timetable, name='timetable-student'),

    path('teacher/', views.teacher, name='timetable-teacher'),
    path('teacher/timetable', views.timetable, name='timetable-teacher'),
    path('teacher/scheduled', views.teacher_scheduled, name='timetable-teacher-scheduled'),
    path('teacher/schedule', views.teacher_scheduler, name='timetable-teacher-schedule'),
]
