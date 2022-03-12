from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import render, redirect

from .models import Lesson, Link, Subject, User, Group


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


@login_required
def timetable(request):
    user = request.user
    lessons = []
    for lesson in Lesson.objects.filter(group_id__link__user_id__username__exact=user.username):
        lesson_data = []
        if user.user_type == 'student':
            lesson_data.append(Subject.objects.filter(link__group_id__lesson__id__exact=lesson.id)[:1].get().name)
            teacher = User.objects.filter(link__group_id__lesson__id__exact=lesson.id, user_type='teacher')[:1].get()
            if teacher.title:
                lesson_data.append(teacher.title.title() + ' ' + teacher.last_name.title())
            else:
                lesson_data.append(teacher.first_name.title() + ' ' + teacher.last_name.title())
        else:
            lesson_data.append(Group.objects.filter(lesson__id__exact=lesson.id)[:1].get().name)
            topic = lesson.topic
            if len(topic) > 32:
                topic = topic[:29]+'...'
            lesson_data.append(topic)
        lesson_data.append('Room')  # Room allocation will be completed later
        start = lesson.start
        end = lesson.start + lesson.duration
        lesson_data.append(start.strftime('%H:%M') + ' - ' + end.strftime('%H:%M'))
        lessons.append(lesson_data)
    print(lessons)
    return render(request, 'timetable/timetable.html', context={'lessons': lessons})



@login_required
def teacher(request):
    return render(request, 'timetable/teacher.html')


@login_required
def teacher_scheduler(request):
    return render(request, 'timetable/scheduling/schedule.html')


@login_required
def teacher_scheduled(request):
    return render(request, 'timetable/scheduling/scheduled_list.html')
