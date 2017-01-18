from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.db.models import Q


import json
import datetime

from kinkcom.models import KinkComSite, KinkComShoot, KinkComPerformer


def shoot(request, shootid=None, title=None, date=None, performer_number=None, performer_name=None):
    return_dict = {'errors':None, 'length':0}
    if shootid == 'latest':
        shoots_ = KinkComShoot.objects.filter(exists=True).latest('shootid')
    elif shootid:
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

    return HttpResponse(json.dumps(return_dict), content_type = 'application/json; charset=utf8')


def performer(request, performer_name=None, performer_number=None):
    return_dict = {'errors': None, 'length': 0}
    if performer_number:
        performers_ = _get_performers_by_number(performer_number)
    elif performer_name:
        performers_ = _get_performers_by_name(performer_name)
    else:
        performers_ = KinkComPerformer.objects.none()

    performers_ = performers_ if performers_ is not None else []
    return_dict['results'] = [s.serialize() for s in performers_]
    return_dict['length'] = performers_.count()
    j_ = json.dumps(return_dict)
    return HttpResponse(j_, content_type = 'application/json; charset=utf8')


def _get_performers_by_number(performer_number):
    try:
        return KinkComPerformer.objects.get(number=performer_number)
    except ObjectDoesNotExist:
        return KinkComPerformer.objects.none()
    except MultipleObjectsReturned:
        performers = KinkComShoot.objects.filter(number=performer_number)
        [p.delete() for p in performers[1:]]
        return performers[0]


def _get_performers_by_name(performer_name):
    return KinkComPerformer.objects.filter(name__regex=performer_name)


def _get_shoots_by_shootid(shootid):
    shoots = KinkComShoot.objects.filter(shootid=shootid)
    if shoots.count() > 1:
        [s.delete() for s in shoots[1:]]
    return shoots


def _get_shoots_by_title(title):
    return KinkComShoot.objects.filter(title__regex=title)


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
