from django.conf.urls import url
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    url(r'^invalid/$', views.invalid, name='invalid'),
    url(r'^response/$', views.response_messages, name='response'),
    url(r'^other/$', views.other_messages, name='other'),
    url(r'^message/([0-9]+)/$', views.message, name='message'),
    url(r'^accepted/$', views.accepted, name='accepted'),
    url(r'^unaccepted/$', views.unaccepted, name='unaccepted'),
    url(r'^response/$', views.response_messages, name='response'),
    url(r'^accept/$', views.accept, name='accept'),
    url(r'^not_accept/$', views.not_accept, name='not_accept'),
    url(r'^next/([0-9]+)/$', views.next, name='next'),
    url(r'^prev/([0-9]+)/$', views.prev, name='prev'),
    url(r'^login/$', views.login, name="login"),
    url(r'^$', views.invalid),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)