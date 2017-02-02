from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^invalid/$', views.invalid, name='invalid'),
    url(r'^response/$', views.response_messages, name='response'),
    url(r'^other/$', views.other_messages, name='other'),
    url(r'^message/([0-9]+)/$', views.message, name='message'),
    url(r'^unaccepted/$', views.unaccepted, name='unaccepted'),
    url(r'^response/$', views.response_messages, name='response'),
    url(r'^accept/$', views.accept, name='accept'),
    url(r'^not_accept/$', views.not_accept, name='not_accept'),
]