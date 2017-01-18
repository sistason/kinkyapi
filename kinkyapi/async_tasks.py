from kinkcom.crawl_kinkcom import KinkComCrawler


def task_update_shoots():
    crawler = KinkComCrawler()
    crawler.update_shoots()


def update_sites(request):
    crawler = KinkComCrawler()
    crawler.update_sites()


