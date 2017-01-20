from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from django.db.models import Q

import json
import datetime

from kinkcom.models import KinkComSite, KinkComShoot, KinkComPerformer


def index(request):
    return_dict = {}

    return render_to_response('kinkcom.html', return_dict, RequestContext(request))


def shoot(request, shootid=None, title=None, date=None, performer_number=None, performer_name=None):
    return_dict = {'errors': None, 'length': 0}
    if shootid is not None:
        shoots_ = _get_shoots_by_shootid(shootid)
    elif title:
        shoots_ = _get_shoots_by_title(title)
    elif date:
        try:
            if date.isdigit():
                date_obj = datetime.date.fromtimestamp(int(date))
            else:
                date_obj = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            shoots_ = _get_shoots_by_date(date_obj)
        except ValueError:
            return_dict['error'] = 'Cannot recognize date format, must be %Y-%m-%d or %s, was "{}"'.format(date)
            shoots_ = KinkComShoot.objects.none()
    elif performer_number:
        shoots_ = _get_shoots_by_performer_number(performer_number)
    elif performer_name:
        shoots_ = _get_shoots_by_performer_name(performer_name)
    else:
        shoots_ = KinkComShoot.objects.none()

    if type(shoots_) == KinkComShoot:
        return_dict['results'] = [shoots_.serialize()]
        return_dict['length'] = 1
    else:
        return_dict['results'] = [s.serialize() for s in shoots_]
        return_dict['length'] = shoots_.count()

    return HttpResponse(json.dumps(return_dict), content_type='application/json; charset=utf8')


def performer(request, performer_name=None, performer_number=None):
    return_dict = {'errors': None, 'length': 0}
    if performer_number:
        performers_ = _get_performers_by_number(performer_number)
    elif performer_name:
        performers_ = _get_performers_by_name(performer_name)
    else:
        performers_ = KinkComPerformer.objects.none()

    return_dict['results'] = [s.serialize() for s in performers_]
    return_dict['length'] = performers_.count()

    return HttpResponse(json.dumps(return_dict), content_type='application/json; charset=utf8')


def site(request, name=None, name_main=None):
    return_dict = {'errors': None, 'length': 0}
    sites_ = _get_sites_by_name(name, name_main)

    return_dict['results'] = [s.serialize() for s in sites_]
    return_dict['length'] = sites_.count()

    return HttpResponse(json.dumps(return_dict), content_type='application/json; charset=utf8')


def _get_sites_by_name(name, name_main):
    if name_main is not None:
        return KinkComSite.objects.filter(is_partner=False).filter(name__iregex=name_main)
    if name is not None:
        return KinkComSite.objects.filter(name__iregex=name)
    return KinkComSite.objects.none()


def _get_performers_by_number(performer_number):
    try:
        return KinkComPerformer.objects.filter(number=performer_number)
    except ObjectDoesNotExist:
        return KinkComPerformer.objects.none()
    except MultipleObjectsReturned:
        performers = KinkComShoot.objects.filter(number=performer_number)
        [p.delete() for p in performers[1:]]
        return performers


def _get_performers_by_name(performer_name):
    return KinkComPerformer.objects.filter(name__iregex=performer_name)


def _get_shoots_by_shootid(shootid):
    if not shootid:
        return KinkComShoot.objects.filter(exists=True).latest('shootid')
    else:
        shoots = KinkComShoot.objects.filter(shootid=shootid)
        if shoots.count() > 1:
            [s.delete() for s in shoots[1:]]
        return shoots


def _get_shoots_by_title(title):
    return KinkComShoot.objects.filter(title__iregex=title)


def _get_shoots_by_date(date_obj):
    return KinkComShoot.objects.filter(date=date_obj)


def _get_shoots_by_performer_number(performer_number):
    return KinkComShoot.objects.filter(performers__number=performer_number)


def _get_shoots_by_performer_name(performer_name):
    shoots_ = Q()
    performers_ = _get_performers_by_name(performer_name)
    for performer_ in performers_:
        shoots = _get_shoots_by_performer_number(performer_.number).values_list('shootid')
        for i in shoots:
            shoots_ |= Q(shootid=i[0])

    if not shoots_:
        return KinkComShoot.objects.none()

    return KinkComShoot.objects.filter(shoots_)


def dump_database(request):
    from kinkyapi.settings import DATABASES, BASE_DIR
    import os
    import subprocess

    app_name = request.path.split('/')[1]
    app_directory = os.path.join(BASE_DIR, app_name)

    database_files = [f.path for f in os.scandir(app_directory) if f.name.startswith('{}_sqldump_'.format(app_name))]
    if database_files and os.path.exists(database_files[0]):
        database_file = database_files[0]
        timestamp = database_file.split('_')[-1].split('.')[0]
        if timestamp.isdigit() and (datetime.datetime.now() - datetime.timedelta(days=1)) \
                <= datetime.datetime.fromtimestamp(int(timestamp)):
            return _return_database_file(database_file)
        else:
            os.remove(database_file)

    database = DATABASES['default']
    now = datetime.datetime.now().strftime('%s')
    dump_location = os.path.join(app_directory, '{}_sqldump_{}.gz'.format(app_name, now))

    config_dict = {'user': database['USER'], 'pw': database['PASSWORD'], 'db_name': database['NAME'],
                    'prefix': app_name}
    tables_cmd = ["mysql", "--user={user}", "--password={pw}", "--skip-column-names",
                  '--execute=SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE \'{prefix}_%\';']
    tables_cmd_formatted = [i.format(**config_dict) for i in tables_cmd]
    tables_cmd_result = subprocess.run(tables_cmd_formatted, stdout=subprocess.PIPE)
    if tables_cmd_result.returncode != 0:
        return HttpResponse(status=500, content="Error while preparing database dump")

    tables = tables_cmd_result.stdout.decode().split('\n')

    dump_cmd = ["mysqldump", "--user={user}", "--password={pw}", "{db_name}"]
    dump_cmd += [i for i in tables if i]
    dump_cmd_formatted = [i.format(**config_dict) for i in dump_cmd]
    gzip_cmd = ["gzip"]

    with open(dump_location, 'wb') as f:
        dump_cmd_ = subprocess.Popen(dump_cmd_formatted, stdout=subprocess.PIPE)
        dump_cmd_result = subprocess.run(gzip_cmd, stdin=dump_cmd_.stdout, stdout=f)
        dump_cmd_.wait()
    if dump_cmd_result.returncode != 0:
        return HttpResponse(status=500, content="Error while dumping database")

    return _return_database_file(dump_location)


def _return_database_file(dump_location):
    from os.path import basename
    with open(dump_location, 'rb') as f:
        dump = f.read()
    response = HttpResponse(dump)
    response['Content-Type'] = 'application/gzip'
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(dump_location))
    return response
