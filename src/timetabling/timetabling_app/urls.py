from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='timetable-home'),

    path('student/login/', views.student_login, name='timetable-student-login'),
    path('student/', views.student_timetable, name='timetable-student'),

    path('teacher/login/', views.teacher_login, name='timetable-teacher-login'),
    path('teacher/', views.teacher_timetable, name='timetable-teacher'),
    path('teacher/schedule', views.teacher_scheduler, name='timetable-teacher-schedule'),

    path('admin/login/', views.admin_login, name='timetable-admin-login'),
    path('admin/', views.admin_timetable, name='timetable-admin'),
]
