from django.shortcuts import render
from mail_parsing.models import EmailAddress, Message, Attachment
from noreply_mail_parsing.settings import BASE_DIR, MEDIA_ROOT
from django.http import HttpResponse
import json


def invalid(request):
    addresses = EmailAddress.objects.all()
    return render(request, 'invalid_addresses.html', {'addresses': addresses})


def message(request, id):
    message = Message.objects.get(id=id)
    files = Attachment.objects.filter(message=message)
    next_id = Message.objects.filter(type=message.type, status=message.status, id__lt=message.id).order_by('-id')
    if len(next_id) > 0:
        next_id = next_id[0].id
    else:
        next_id = -1
    prev_id = Message.objects.filter(type=message.type, status=message.status, id__gt=message.id).order_by('id')
    if len(prev_id) > 0:
        prev_id = prev_id[0].id
    else:
        prev_id = -1
    return render(request, 'message.html', {'message': message,
                                            'files': files,
                                            'path': 'file://'+MEDIA_ROOT+'/',
                                            'next': next_id,
                                            'prev': prev_id})


def response_messages(request):
    messages = Message.objects.filter(type=0,status=2).order_by('-id')
    return render(request, 'table.html', {'messages': messages})


def other_messages(request):
    messages = Message.objects.filter(type=1,status=2).order_by('-id')
    return render(request, 'table.html', {'messages': messages})


def unaccepted(request):
    messages = Message.objects.filter(status=1).order_by('-id')
    return render(request, 'table.html', {'messages': messages})

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

