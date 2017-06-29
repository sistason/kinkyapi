from django.http import HttpResponse
from django_q.tasks import async
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from kinkcom.crawl_kinkcom import KinkComCrawler


def index(request):
    return_dict = {'apis': [{'name':'Kink.com', 'url': '/kinkcom'}]}

    return render_to_response('index.html', return_dict, RequestContext(request))


@login_required
def get_shoot(request, shootid=None):
    crawler = KinkComCrawler()
    shoot = crawler.get_shoot(shootid)

    return HttpResponse(shoot.title)


def update_sites(request):
    _ip = request.META.get('HTTP_X_FORWARDED_FOR','') if request.META.get('HTTP_X_FORWARDED_FOR','') else request.META.get('REMOTE_ADDR','')
    if _ip == '78.46.152.225':
        async('kinkyapi.async_tasks.task_update_sites')
        return HttpResponse("200 - Task queried")
    return HttpResponse("Not found", status=404)


def update_shoots(request):
    _ip = request.META.get('HTTP_X_FORWARDED_FOR','') if request.META.get('HTTP_X_FORWARDED_FOR','') else request.META.get('REMOTE_ADDR','')
    if _ip == '78.46.152.225':
        async('kinkyapi.async_tasks.task_update_shoots')
        return HttpResponse("200 - Task queried")
    return HttpResponse("Not found", status=404)
