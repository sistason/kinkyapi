from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import render_to_response
from django.http import HttpResponse, JsonResponse
from django.template import RequestContext

import re
import os
import json
import datetime

from kinkcom.models import KinkComSite, KinkComShoot, KinkComPerformer
from kinkyapi.settings import BASE_DIR


def index(request):
    return_dict = {}

    return render_to_response('kinkcom.html', return_dict, RequestContext(request))


def shoot(request, shootid=None, title=None, date=None, performer_numbers=None, performer_name=None):
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
    elif performer_numbers:
        shoots_ = _get_shoots_by_performer_numbers(performer_numbers)
    elif performer_name:
        shoots_ = _get_shoots_by_performer_names(performer_name)
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
    except (ObjectDoesNotExist, ValueError):
        return KinkComPerformer.objects.none()
    except MultipleObjectsReturned:
        performers = KinkComShoot.objects.filter(number=performer_number)
        [p.delete() for p in performers[1:]]
        return performers


def _get_performers_by_name(performer_name):
    if ',' in performer_name:
        performer_name = re.sub(r',', _replace_repetitions_with_or, performer_name)
        performer_name = '|'.join(p.strip() for p in performer_name.split('|'))
    return KinkComPerformer.objects.filter(name__iregex=performer_name)


def _replace_repetitions_with_or(match):
    """ Replaces a comma only if it is not a comma in an repetition statement """
    if re.match(r'\{\d,\d?\}', match.string[match.start()-2:match.end()+2]):
        return 'r'
    return '|'


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


def _get_shoots_by_performer_numbers(performer_numbers):
    all = KinkComShoot.objects.all()
    for number in re.split(r'\D', performer_numbers):
        all = all.filter(performers__number=number)
    return all


def _get_shoots_by_performer_names(performer_name):
    performers_ = _get_performers_by_name(performer_name)
    performer_numbers_ = ','.join(str(v[0]) for v in performers_.values_list('number'))
    return _get_shoots_by_performer_numbers(performer_numbers_)


def dump_database(request):
    from kinkyapi.settings import DATABASES
    app_name = request.path.split('/')[1]
    app_directory = os.path.join(BASE_DIR, app_name)

    dump_name = 'sqldump'
    dump_file, dump_is_current = _get_dump_file(app_name, app_directory, dump_name)
    if dump_file and dump_is_current:
        return _return_database_file(dump_file)
    if dump_file:
        os.remove(dump_file)

    database = DATABASES['default']
    now = datetime.datetime.now().strftime('%s')
    dump_location = os.path.join(app_directory, '{}_{}_{}.gz'.format(app_name, dump_name, now))
    config_dict = {'user': database['USER'], 'pw': database['PASSWORD'], 'db_name': database['NAME'],
                   'prefix': app_name}

    tables = _dump_database_get_tables(config_dict)
    if not tables:
        return HttpResponse(status=500, content="Error while preparing database dump")

    dump_success = _dump_database_dump_and_gzip_db(config_dict, dump_location, tables)
    if not dump_success:
        return HttpResponse(status=500, content="Error while dumping database")

    return _return_database_file(dump_location)


def _dump_database_dump_and_gzip_db(config_dict, dump_location, tables):
    import subprocess
    dump_cmd = ["mysqldump", "--user={user}", "--password={pw}", "{db_name}"]
    dump_cmd += [i for i in tables if i]
    dump_cmd_formatted = [i.format(**config_dict) for i in dump_cmd]
    gzip_cmd = ["gzip"]
    with open(dump_location, 'wb') as f:
        dump_cmd_ = subprocess.Popen(dump_cmd_formatted, stdout=subprocess.PIPE)
        dump_cmd_result = subprocess.run(gzip_cmd, stdin=dump_cmd_.stdout, stdout=f)
        dump_cmd_.wait()
    if dump_cmd_result.returncode == 0:
        return True


def _dump_database_get_tables(config_dict):
    import subprocess

    tables_cmd = ["mysql", "--user={user}", "--password={pw}", "--skip-column-names",
                  '--execute=SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE \'{prefix}_%\';']
    tables_cmd_formatted = [i.format(**config_dict) for i in tables_cmd]
    tables_cmd_result = subprocess.run(tables_cmd_formatted, stdout=subprocess.PIPE)
    if tables_cmd_result.returncode == 0:
        return tables_cmd_result.stdout.decode().split('\n')


def _return_database_file(dump_location):
    from os.path import basename
    with open(dump_location, 'rb') as f:
        dump = f.read()
    response = HttpResponse(dump)
    response['Content-Type'] = 'application/gzip'
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(dump_location))
    return response


def dump_shoots(request):
    dump_name = 'shoots'
    j_ = _dump_json(request, dump_name)
    return JsonResponse(j_, safe=False)


def _dump_and_get_json(app_directory, app_name, dump_name, all_data):
    now = datetime.datetime.now().strftime('%s')
    dump_location = os.path.join(app_directory, '{}_{}_{}.json'.format(app_name, dump_name, now))

    data = [d.serialize() for d in all_data]

    j_dump = json.dumps(data)
    with open(dump_location, 'w') as f:
        f.write(j_dump)

    return j_dump


def _get_dump_file(app_name, app_directory, dump_name):
    dump_files = [f.path for f in os.scandir(app_directory) if f.name.startswith('{}_{}_'.format(app_name, dump_name))]
    if dump_files and os.path.exists(dump_files[0]):
        dump_file = dump_files[0]
        timestamp = dump_file.split('_')[-1].split('.')[0]
        if timestamp.isdigit() and (datetime.datetime.now() - datetime.timedelta(days=1)) \
                <= datetime.datetime.fromtimestamp(int(timestamp)):

            return dump_file, True
        else:
            return dump_file, False

    return None, False


def dump_performers(request):
    dump_name = 'performers'
    j_ = _dump_json(request, dump_name)
    return JsonResponse(j_, safe=False)


def dump_sqlite(request):
    from kinkyapi.settings import BASE_DIR
    app_name = request.path.split('/')[1]
    app_directory = os.path.join(BASE_DIR, app_name)

    dump_name = 'sqlite3dump'
    dump_file, dump_is_current = _get_dump_file(app_name, app_directory, dump_name)
    if dump_file and dump_is_current:
        return _return_database_file(dump_file)
    if dump_file:
        os.remove(dump_file)

    db_response = dump_database(request)
    mysql_location = os.path.join(app_directory, db_response['Content-Disposition'][22:-1])

    now = datetime.datetime.now().strftime('%s')
    dump_location = os.path.join(app_directory, '{}_{}_{}'.format(app_name, dump_name, now))

    import subprocess
    import shutil
    shutil.copy(mysql_location, mysql_location+'2.gz')
    subprocess.run(["gunzip", mysql_location+'2.gz'])
    conversion_cmd = subprocess.Popen(["mysql2sqlite", mysql_location+'2'], stdout=subprocess.PIPE)
    subprocess.run(["sqlite3", dump_location], stdin=conversion_cmd.stdout)
    conversion_cmd.wait()
    dump_cmd_result = subprocess.run(["gzip", dump_location])
    os.remove(mysql_location+'2')

    if dump_cmd_result.returncode == 0:
        return _return_database_file(dump_location+'.gz')
    return HttpResponse(status=500, content="Error while preparing database dump")


def dump_models_py(request):
    file_path = os.path.join(BASE_DIR, 'kinkcom', 'models.py')

    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="text/x-python")
        response['Content-Disposition'  ] = 'inline; filename=models.py'
        return response


def dump_sites(request):
    dump_name = 'sites'
    j_ = _dump_json(request, dump_name)
    return JsonResponse(j_, safe=False)


def _dump_json(request, dump_name):
    app_name = request.path.split('/')[1]
    app_directory = os.path.join(BASE_DIR, app_name)

    dump_file, dump_is_current = _get_dump_file(app_name, app_directory, dump_name)
    if dump_file and dump_is_current:
        with open(dump_file, 'r') as f:
            j_dump = f.read()
        return j_dump

    if dump_file:
        os.remove(dump_file)

    all_data = _get_all(dump_name)
    j_dump = _dump_and_get_json(app_directory, app_name, dump_name, all_data)
    return j_dump


def _get_all(dump_name):
    if dump_name == 'sites':
        return _get_sites_by_name(r'.*', None)
    if dump_name == 'shoots':
        return _get_shoots_by_title(r'.*')
    if dump_name == 'performers':
        return _get_performers_by_name(r'.*')


def dump_all(request):
    everything = {dump_name: dump_json(request, dump_name) for dump_name in ['sites', 'shoots', 'performers']}
    return JsonResponse(everything, safe=False)
