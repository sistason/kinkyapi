from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^shoot/(?P<shootid>\d*|latest)$', views.shoot, name='shoot'),
    url(r'^shoot_title/(?P<title>.+)$', views.shoot, name='shoot'),
    url(r'^shoot_date/(?P<date>.+)$', views.shoot, name='shoot'),
    url(r'^shoot_performer/(?P<performer_number>\d+)$', views.shoot, name='shoot'),
    url(r'^shoot_performer_name/(?P<performer_name>.+)$', views.shoot, name='shoot'),

    url(r'^performer/(?P<performer_number>\d+)$', views.performer, name='performer'),
    url(r'^performer_name/(?P<performer_name>.+)$', views.performer, name='performer'),

]