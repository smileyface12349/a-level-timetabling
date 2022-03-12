from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import render, redirect


# def home(request):
#     return render(request, 'timetable/home.html')

# def student_login(request):
#     return render(request, 'timetable/login.html', {'user_type': 'student', 'user_opposite': 'teacher'})

# def teacher_login(request):
#     return render(request, 'timetable/login.html', {'user_type': 'teacher', 'user_opposite': 'student'})


def login_redirect(request):
    # redirect appropriately depending on user type
    user = request.user
    if isinstance(user, AnonymousUser):
        return redirect('/login/')
    else:
        if user.user_type == 'student':
            return redirect('/student/')
        elif user.user_type == 'teacher':
            return redirect('/teacher/')
        else:
            return redirect('/admin/')

    # headers = request.META
    # if 'REMOTE_HOST' in headers:
    #     user = headers['REMOTE_HOST']
    #     print(user)
    #     if user.user_type == 'student':
    #         return redirect('/student/')
    #     elif user.user_type == 'teacher':
    #         return redirect('/teacher/')
    #     else:
    #         return redirect('/admin/')
    # else:
    #     return redirect('/login/')


@login_required
def student_timetable(request):
    return render(request, 'timetable/timetable.html')


@login_required
def teacher(request):
    return render(request, 'timetable/teacher.html')


@login_required
def teacher_timetable(request):
    return render(request, 'timetable/timetable.html')


@login_required
def teacher_scheduler(request):
    return render(request, 'timetable/scheduling/schedule.html')


@login_required
def teacher_scheduled(request):
    return render(request, 'timetable/scheduling/scheduled_list.html')
