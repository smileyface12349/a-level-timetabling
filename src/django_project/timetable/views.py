from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return render(request, 'timetable/home.html')


def student_login(request):
    return render(request, 'timetable/login.html', {'user_type': 'student', 'user_opposite': 'teacher'})


def student_timetable(request):
    return render(request, 'timetable/timetable.html')


def teacher_login(request):
    return render(request, 'timetable/login.html', {'user_type': 'teacher', 'user_opposite': 'student'})


def teacher(request):
    return render(request, 'timetable/teacher.html')


def teacher_timetable(request):
    return render(request, 'timetable/timetable.html')


def teacher_scheduler(request):
    return render(request, 'timetable/scheduling/schedule.html')


def teacher_scheduled(request):
    return render(request, 'timetable/scheduling/scheduled_list.html')
