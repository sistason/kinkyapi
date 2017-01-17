from django.http import HttpResponse


from kinkcom.crawl_kinkcom import KinkComCrawler
from kinkcom.models import KinkComShoot, KinkComPerformer, KinkComSite
from kinkyapi.async_tasks import task_update_shoots

from django_q.tasks import async, result


def index(request):
    crawler = KinkComCrawler()
    shoot = crawler.get_shoot(17341)
    return HttpResponse(str(shoot))


def update_sites(request):
    crawler = KinkComCrawler()
    old_size = KinkComSite.objects.count()
    crawler.update_sites()

    return HttpResponse("200 - {} new sites".format(KinkComSite.objects.count()-old_size))


def get_shoot(request, shootid=None):
    crawler = KinkComCrawler()
    shoot = crawler.get_shoot(shootid)

    return HttpResponse(shoot.title)


def update_shoots(request):
    async('kinkyapi.async_tasks.task_update_shoots')
    return HttpResponse(200)
