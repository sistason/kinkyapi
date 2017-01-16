from django.http import HttpResponse

from kinkcom.crawl_kinkcom import KinkComCrawler

def index(request):
    crawler = KinkComCrawler()
    shoot = crawler.get_shoot(17341)
    return HttpResponse(str(shoot))