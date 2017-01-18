from django.http import HttpResponse
from django_q.tasks import async

from kinkcom.crawl_kinkcom import KinkComCrawler


def index(request):
    crawler = KinkComCrawler()
    shoot = crawler.get_shoot(17341)
    return HttpResponse(str(shoot))


def get_shoot(request, shootid=None):
    crawler = KinkComCrawler()
    shoot = crawler.get_shoot(shootid)

    return HttpResponse(shoot.title)


def update_sites(request):
    async('kinkyapi.async_tasks.task_update_sites')
    return HttpResponse("200 - Task queried")


def update_shoots(request):
    async('kinkyapi.async_tasks.task_update_shoots')
    return HttpResponse("200 - Task queried")
