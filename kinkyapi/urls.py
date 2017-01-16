from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^_update_sites/$', views.update_sites, name='update_sites'),
    url(r'^_update_shoots/$', views.update_shoots, name='update_shoots'),
]

urlpatterns += [
    url(r'^kinkcom/', include('kinkcom.urls')),
]