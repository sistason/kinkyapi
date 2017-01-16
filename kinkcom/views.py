from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import render_to_response
from django.http import HttpResponse

import json
import datetime

from kinkcom.models import KinkComSite, KinkComShoot, KinkComPerformer


def shoot(request, shootid=None, title=None, date=None, performer_number=None, performer_name=None):
    if shootid:
        shoots_ = _get_shoots_by_shootid(shootid)
    elif title:
        shoots_ = _get_shoots_by_title(title)
    elif date:
        try:
            if date.isdigit():
                date_obj = datetime.date.fromtimestamp(date)
            else:
                date_obj = datetime.datetime.strptime(date, '%B %d, %Y').date()
            shoots_ = _get_shoots_by_date(date_obj)
        except ValueError:
            shoots_ = {'error': 'Cannot recognize date format, must be "%B %d, %Y", was "{}"'.format(date)}
    elif performer_number:
        shoots_ = _get_shoots_by_performer_number(performer_number)
    elif performer_name:
        shoots_ = _get_shoots_by_performer_name(performer_name)
    else:
        shoots_ = None

    shoots_ = shoots_ if shoots_ else []
    j_ = json.dumps(shoots_)
    return HttpResponse(j_, content_type = 'application/json; charset=utf8')


def performer(request, performer_name=None, performer_number=None):
    if performer_number:
        performer_ = _get_performers_by_number(performer_number)
    elif performer_name:
        performer_ = _get_performers_by_name(performer_name)
    else:
        performer_ = None

    performer_ = performer_ if performer_ is not None else []
    j_ = json.dumps(performer_)
    return HttpResponse(j_, content_type = 'application/json; charset=utf8')


def _get_performers_by_number(performer_number):
    try:
        return KinkComPerformer.objects.get(number=performer_number)
    except ObjectDoesNotExist:
        return None
    except MultipleObjectsReturned:
        performers = KinkComShoot.objects.filter(number=performer_number)
        [p.delete() for p in performers[1:]]
        return performers[0]


def _get_performers_by_name(performer_name):
    return KinkComPerformer.objects.filter(name__regex=performer_name)


def _get_shoots_by_shootid(shootid):
    try:
        return KinkComShoot.objects.get(shootid=shootid)
    except ObjectDoesNotExist:
        return None
    except MultipleObjectsReturned:
        shoots = KinkComShoot.objects.filter(shootid=shootid)
        [s.delete() for s in shoots[1:]]
        return shoots[0]


def _get_shoots_by_title(title):
    return KinkComShoot.objects.filter(title__regex=title)


def _get_shoots_by_date(date_obj):
    return KinkComShoot.objects.filter(date=date_obj)


def _get_shoots_by_performer_number(performer_number):
    return KinkComShoot.objects.filter(performer__number=performer_number)


def _get_shoots_by_performer_name(performer_name):
    shoots = []
    performers_ = _get_performers_by_name(performer_name)
    for performer_ in performers_:
        shoots.append(_get_shoots_by_performer_number(performer_.number))
    return shoots