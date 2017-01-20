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


@login_required
def update_sites(request):
    async('kinkyapi.async_tasks.task_update_sites')
    return HttpResponse("200 - Task queried")


@login_required
def update_shoots(request):
    async('kinkyapi.async_tasks.task_update_shoots')
    return HttpResponse("200 - Task queried")
