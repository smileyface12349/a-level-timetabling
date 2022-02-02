from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='timetable-home'),

    path('student/login/', views.student_login, name='timetable-student-login'),
    path('student/', views.student_timetable, name='timetable-student'),

    path('teacher/login/', views.teacher_login, name='timetable-teacher-login'),
    path('teacher/', views.teacher_timetable, name='timetable-teacher'),
    path('teacher/scheduled', views.teacher_scheduled, name='timetable-teacher-scheduled'),
    path('teacher/schedule', views.teacher_scheduler, name='timetable-teacher-schedule'),
]
