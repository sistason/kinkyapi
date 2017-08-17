from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^shoot/(?P<shootid>\d*)$', views.shoot, name='shoot'),
    url(r'^shoot_shootid/(?P<shootid>\d*)$', views.shoot, name='shoot'),
    url(r'^shoot_title/(?P<title>.+)$', views.shoot, name='shoot'),
    url(r'^shoot_date/(?P<date>[-\d]+)$', views.shoot, name='shoot'),
    url(r'^shoot_performers/(?P<performer_numbers>.*)$', views.shoot, name='shoot'),
    url(r'^shoot_performers_number/(?P<performer_numbers>.*)$', views.shoot, name='shoot'),
    url(r'^shoot_performers_names/(?P<performer_name>.+)$', views.shoot, name='shoot'),

    url(r'^performer/(?P<performer_number>\d+)$', views.performer, name='performer'),
    url(r'^performer_number/(?P<performer_number>\d+)$', views.performer, name='performer'),
    url(r'^performer_name/(?P<performer_name>.+)$', views.performer, name='performer'),

    url(r'^site/(?P<name>.*)$', views.site, name='site'),
    url(r'^site_name/(?P<name>.*)$', views.site, name='site'),
    url(r'^site_main/(?P<name_main>.*)$', views.site, name='site'),

    url(r'^dump_db/?$', views.dump_database, name='dump_database'),
    url(r'^dump_sqlite/?$', views.dump_sqlite, name='dump_sqlite'),
    url(r'^dump_sites/?$', views.dump_sites, name='dump_sites'),
    url(r'^dump_all/?$', views.dump_all, name='dump_all'),
    url(r'^dump_shoots/?$', views.dump_shoots, name='dump_shoots'),
    url(r'^dump_performers/?$', views.dump_performers, name='dump_performers'),
    url(r'^dump_models.py/?$', views.dump_models_py, name='dump_models_py'),
]