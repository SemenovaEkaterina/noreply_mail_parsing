from django.shortcuts import render
from mail_parsing.models import EmailAddress, Message, Attachment
from noreply_mail_parsing.settings import BASE_DIR, MEDIA_ROOT
from django.http import HttpResponse
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.contrib import auth
from .forms import LoginForm
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login/')
def invalid(request):
    addresses = EmailAddress.objects.all()
    count = addresses.count()
    addresses, max_page = paginate(addresses, request)
    return render(request, 'invalid_addresses.html', {'addresses': addresses,
                                                      'range': get_range(addresses.number, max_page),
                                                      'count': count})


@login_required(login_url='/login/')
def message(request, id):
    message = Message.objects.get(id=id)
    files = Attachment.objects.filter(message=message)

    if request.GET.get('status') is not None:
        list_status = request.GET.get('status')
        if request.GET.get('type') is not None:
            list_type = request.GET.get('type')
        else:
            list_type = -1
    else:
        list_status = -1
        list_type = -1

    return render(request, 'message.html', {'message': message,
                                            'files': files,
                                            'path': 'file://'+MEDIA_ROOT+'/',
                                            'list_type': list_type,
                                            'list_status': list_status})


@login_required(login_url='/login/')
def response_messages(request):
    type_of_list = '?'
    for param in request.GET.keys():
        type_of_list += param + '=' + request.GET[param] + '&'
    messages = Message.objects.filter(type=0,status=2).order_by('-id')
    count = messages.count()
    messages, max_page = paginate(messages, request)
    return render(request, 'table.html', {'messages': messages,
                                          'range': get_range(messages.number, max_page),
                                          'count': count,
                                          'type_of_list': type_of_list})


@login_required(login_url='/login/')
def other_messages(request):
    type_of_list = '?'
    for param in request.GET.keys():
        type_of_list += param + '=' + request.GET[param] + '&'
    messages = Message.objects.filter(type=1,status=2).order_by('-id')
    count = messages.count()
    messages, max_page = paginate(messages, request)
    return render(request, 'table.html', {'messages': messages,
                                          'range': get_range(messages.number, max_page),
                                          'count': count,
                                          'type_of_list': type_of_list})


@login_required(login_url='/login/')
def accepted(request):
    type_of_list = '?'
    for param in request.GET.keys():
        type_of_list += param + '=' + request.GET[param] + '&'
    messages = Message.objects.filter(status=0).order_by('-id')
    count = messages.count()
    messages, max_page = paginate(messages, request)
    return render(request, 'table.html', {'messages': messages,
                                          'range': get_range(messages.number, max_page),
                                          'count': count,
                                          'type_of_list': type_of_list})


@login_required(login_url='/login/')
def unaccepted(request):
    type_of_list = '?'
    for param in request.GET.keys():
        type_of_list += param + '=' + request.GET[param] + '&'
    messages = Message.objects.filter(status=1).order_by('-id')
    count = messages.count()
    messages, max_page = paginate(messages, request)
    return render(request, 'table.html', {'messages': messages,
                                          'range': get_range(messages.number, max_page),
                                          'count': count,
                                          'type_of_list': type_of_list})


@login_required(login_url='/login/')
def accept(request):
    id = request.POST.get('id')
    message_object = Message.objects.get(id=id)
    message_object.status = 0
    message_object.save()
    response_data = {'status': 'OK'}
    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )


@login_required(login_url='/login/')
def not_accept(request):
    id = request.POST.get('id')
    message_object = Message.objects.get(id=id)
    message_object.status = 1
    message_object.save()
    response_data = {'status': 'OK'}
    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )

@login_required(login_url='/login/')
def next(request, current_id):
    type_of_list = '?'
    if request.GET.get('status') is not None:
        list_status = request.GET.get('status')
        type_of_list += 'status=' + list_status + '&'
        if request.GET.get('type') is not None:
            list_type = request.GET.get('type')
            type_of_list += 'type=' + list_type + '&'
            try:
                next_id = Message.objects.filter(type=list_type, status=list_status, id__lt=current_id).order_by(
                '-id')[0].id
            except IndexError:
                return HttpResponseRedirect('/')
        else:
            list_type = -1

            try:
                next_id = Message.objects.filter(status=list_status, id__lt=current_id).order_by(
                    '-id')[0].id
            except IndexError:
                return HttpResponseRedirect('/')
    else:
        next_id = current_id

    return HttpResponseRedirect('/message/'+str(next_id)+str(type_of_list))

@login_required(login_url='/login/')
def prev(request, current_id):
    type_of_list = '?'
    if request.GET.get('status') is not None:
        list_status = request.GET.get('status')
        type_of_list += 'status=' + list_status + '&'
        if request.GET.get('type') is not None:
            list_type = request.GET.get('type')
            type_of_list += 'type=' + list_type + '&'
            try:
                prev_id = Message.objects.filter(type=list_type, status=list_status, id__gt=current_id).order_by(
                'id')[0].id
            except IndexError:
                return HttpResponseRedirect('/')
        else:
            list_type = -1

            try:
                prev_id = Message.objects.filter(status=list_status, id__gt=current_id).order_by(
                    'id')[0].id
            except IndexError:
                return HttpResponseRedirect('/')
    else:
        prev_id = current_id

    return HttpResponseRedirect('/message/'+str(prev_id)+str(type_of_list))


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = auth.authenticate(username=form.cleaned_data['login'],
                                     password=form.cleaned_data['password'])
            if user is not None:
                auth.login(request, user)
                return HttpResponseRedirect(str('/'))
            else:
                form.add_error(None, 'invalid login/password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def paginate(objects_list, request):
    paginator = Paginator(objects_list, 50)
    page = request.GET.get('page')
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
    return objects, paginator.num_pages

def get_range(page, max_page):
    page = int(page)
    limits = []
    for i in range(-2, 3):
        if (0 < page + i <= max_page):
            limits.append(page + i)
    return limits

