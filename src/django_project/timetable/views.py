import datetime
import math

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import render, redirect

from .forms import ScheduleForm
from .models import Lesson, Subject, User, Group

MIN_UNSCHEDULED_LESSONS = 3

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
    day = request.GET.get('day')

    if day and day.isdigit():  # user could have modified it to not be an int
        day = int(day)
        current_date = datetime.datetime.utcfromtimestamp(int(day))
    else:
        current_date = datetime.datetime.utcnow()
    weekday: int = current_date.weekday()
    if weekday >= 5:
        current_date = current_date + datetime.timedelta(days=7-weekday)
        weekday = 0
    weekstart = current_date - datetime.timedelta(days=weekday)
    after = current_date.replace(hour=0, minute=0, second=0)
    before = current_date.replace(hour=23, minute=59, second=59)
    weeks_diff = math.floor((current_date - datetime.datetime.utcnow()).days / 7)

    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    if weeks_diff <= -2:
        weekdays_links = {'<': 'disabled'}
    else:
        weekdays_links = {'<': math.floor((weekstart - datetime.timedelta(days=3)).timestamp())}
    for i in range(5):
        d = weekstart + datetime.timedelta(days=i)
        if i == weekday:
            key = weekdays[i]+' '+str(d.day)
            weekday_format = key
        else:
            key = weekdays[i]
        weekdays_links[key] = math.floor(d.timestamp())
    if weeks_diff >= 2:
        weekdays_links['>'] = 'disabled'
    else:
        weekdays_links['>'] = math.floor((weekstart + datetime.timedelta(days=7)).timestamp())

    lessons = []

    for lesson in Lesson.objects.filter(group_id__link__user_id__username__exact=user.username, start__gte=after, start__lte=before).order_by('start'):
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
            if len(topic) > 44:
                topic = topic[:42]+'...'
            lesson_data.append(topic)
        lesson_data.append('Room')  # Room allocation will be completed later
        start = lesson.start
        end = lesson.start + lesson.duration
        lesson_data.append(start.strftime('%H:%M') + ' - ' + end.strftime('%H:%M'))
        lessons.append(lesson_data)

    return render(request, 'timetable/timetable.html', context={'lessons': lessons, 'weekday_format': weekday_format, 'weekdays_links': weekdays_links})


@login_required
def teacher(request):
    return render(request, 'timetable/teacher.html')


@login_required
def teacher_scheduler(request):
    if request.method == 'POST':
        form = ScheduleForm(request.POST, request=request)
        if form.is_valid():
            Lesson.objects.create(duration=form.cleaned_data['duration'], topic=form.cleaned_data['topic'],
                                  group=form.cleaned_data['group'])
            return redirect('/teacher/scheduled')

    else:
        form = ScheduleForm(request=request, label_suffix='')

    return render(request, 'timetable/scheduling/schedule.html', {'form': form})


@login_required
def teacher_scheduled(request):
    user = request.user

    lessons = []
    unscheduled = 0
    for lesson in Lesson.objects.filter(group_id__link__user_id__username__exact=user.username).exclude(start__lte=datetime.datetime.now()).order_by('id'):

        hours = math.floor(lesson.duration.seconds / 3600)
        minutes = math.floor((lesson.duration.seconds - hours*3600) / 60)

        if lesson.topic:
            topic = lesson.topic
        else:
            topic = '[untitled]'  # this makes more sense than an empty string

        if not lesson.fixed:
            unscheduled += 1

        lessons.append({'topic': topic, 'duration': str(hours)+'h '+str(minutes)+'m', 'fixed': lesson.fixed})

    return render(request, 'timetable/scheduling/scheduled_list.html', {'lessons': lessons, 'enough': unscheduled >= MIN_UNSCHEDULED_LESSONS})
