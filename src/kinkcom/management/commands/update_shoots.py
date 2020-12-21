import logging

from django.core.management.base import BaseCommand

from kinkcom.crawl_kinkcom import KinkComCrawler

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    logging.basicConfig(level=logging.DEBUG)

    help = "Update shoots, e.g. get latest/missing shoots"

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)

        crawler = KinkComCrawler()
        crawler.update_shoots()
