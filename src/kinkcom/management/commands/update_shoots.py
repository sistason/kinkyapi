import logging

from django.core.management.base import BaseCommand

from kinkcom.crawl_kinkcom import KinkComCrawler

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    logging.basicConfig(level=logging.DEBUG)

    help = "Update shoots, e.g. get latest/missing shoots"

    def add_arguments(self, parser):
        parser.add_argument('--sleep', type=int)

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)

        crawler = KinkComCrawler()
        crawler.update_shoots()

        if options.get('sleep'):
            # easy way to sleep after execution to run in a while true / restart: always
            import time
            time.sleep(options['sleep'])
