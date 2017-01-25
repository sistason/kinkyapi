from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^shoot/(?P<shootid>\d*)$', views.shoot, name='shoot'),
    url(r'(?s)^shoot_title/(?P<title>.+)$', views.shoot, name='shoot'),
    url(r'^shoot_date/(?P<date>.+)$', views.shoot, name='shoot'),
    url(r'^shoot_performers/(?P<performer_numbers>.*)$', views.shoot, name='shoot'),
    url(r'(?s)^shoot_performer_name/(?P<performer_name>.+)$', views.shoot, name='shoot'),

    url(r'^performer/(?P<performer_number>\d+)$', views.performer, name='performer'),
    url(r'(?s)^performer_name/(?P<performer_name>.+)$', views.performer, name='performer'),

    url(r'^site/(?P<name>.*)$', views.site, name='site'),
    url(r'^site_main/(?P<name_main>.*)$', views.site, name='site'),

    url(r'^dump_db/?$', views.dump_database, name='dump_database'),
    url(r'^dump_shoots/?$', views.dump_shoots, name='dump_shoots'),
    url(r'^dump_models/?$', views.dump_performers, name='dump_performers'),
]