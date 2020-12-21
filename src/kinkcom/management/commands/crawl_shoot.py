import logging

from django.core.management.base import BaseCommand

from kinkcom.crawl_kinkcom import KinkComCrawler

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    logging.basicConfig(level=logging.DEBUG)

    help = "Crawls specified shoot"

    def add_arguments(self, parser):
        parser.add_argument('shoot_id', type=int)

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.DEBUG)

        crawler = KinkComCrawler()
        print(crawler.get_shoot(options['shoot_id']))
