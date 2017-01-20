from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^shoot/(?P<shootid>\d*)$', views.shoot, name='shoot'),
    url(r'(?s)^shoot_title/(?P<title>.+)$', views.shoot, name='shoot'),
    url(r'^shoot_date/(?P<date>.+)$', views.shoot, name='shoot'),
    url(r'^shoot_performer/(?P<performer_number>\d+)$', views.shoot, name='shoot'),
    url(r'(?s)^shoot_performer_name/(?P<performer_name>.+)$', views.shoot, name='shoot'),

    url(r'^performer/(?P<performer_number>\d+)$', views.performer, name='performer'),
    url(r'(?s)^performer_name/(?P<performer_name>.+)$', views.performer, name='performer'),

    url(r'^site/(?P<name>.*)$', views.site, name='site'),
    url(r'^site_main/(?P<name_main>.*)$', views.site, name='site'),

    url(r'^dump/?$', views.dump_database, name='dump_database'),
]