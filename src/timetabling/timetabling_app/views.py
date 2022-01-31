from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return HttpResponse("Here will be a basic homepage giving links to the other sites")


def student_login(request):
    return HttpResponse("This will process student logins")


def student_timetable(request):
    return HttpResponse("This will display student timetables")


def teacher_login(request):
    return HttpResponse("This will process teacher logins")


def teacher_timetable(request):
    return HttpResponse("This will display teacher timetables")


def teacher_scheduler(request):
    return HttpResponse("This will allow teachers to schedule lessons")


def admin_login(request):
    return HttpResponse("This will process admin logins")


def admin_timetable(request):
    return HttpResponse("This will display the overall timetable")
