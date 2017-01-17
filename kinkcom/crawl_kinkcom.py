#!/usr/bin/env python3

import requests
import logging
logging.basicConfig(format='%(funcName)s: %(message)s',
                level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
import bs4
import datetime

from django.core.exceptions import ObjectDoesNotExist
from kinkcom.models import KinkComSite, KinkComShoot, KinkComPerformer


class KinkyCrawler:
    shoot_url = '<unset>'

    def __init__(self):
        self._cookies = None
        self._headers = None

        self.set_headers()

    def set_headers(self):
        # TODO: randomized user-agent
        self._headers = {'Accept-Language': 'en-US,en;q=0.5'}

    def set_cookies(self):
        return NotImplementedError

    def get_shoot(self, shootid):
        return NotImplementedError

    def get_newest_shoot(self):
        return 0

    def update_sites(self):
        return NotImplementedError

    def update_shoots(self):
        all_shoots = KinkComShoot.objects.all()
        end = self.get_newest_shoot()
        for i in range(end):
            logging.info('Updating shoot {}/{}'.format(i, end))
            if all_shoots.filter(shootid=i).exists():
                logging.info('\tShoot already exists')
                continue
            self.get_shoot(i)

    def make_request_get(self, url, data=None):
        if data is None:
            data = {}
        if not self._cookies:
            self.set_cookies()

        url = self.shoot_url + url
        ret = ''
        retries = 3
        while not ret and retries > 0:
            try:
                r_ = requests.get(url, data=data, cookies=self._cookies, headers=self._headers, timeout=2)
                ret = r_.text
            except requests.Timeout:
                retries -= 1
            except Exception as e:
                logging.debug('Caught Exception "{}" while making a get-request to "{}"'.format(e, url))
                break
        return ret


class KinkComCrawler(KinkyCrawler):
    name = 'Kink.com'
    shoot_url = 'https://www.kink.com/'

    def set_cookies(self):
        _ret = requests.get(self.shoot_url)
        _cookies = _ret.cookies
        _cookies['viewing-preferences'] = 'straight,gay'
        self._cookies = _cookies

    def get_performer(self, id_):
        content = self.make_request_get("model/{}".format(id_))
        _bs = bs4.BeautifulSoup(content, "html5lib")
        if _bs.title.text != "Error":
            name_ = _bs.title.text
            data_ = _bs.find('table', attrs={'class': "model-data"})
            performer, _ = KinkComPerformer.objects.get_or_create(name=name_, number=id_)
            performer.fill_model_data(model_data=data_)
            return performer

        return None

    def update_sites(self):
        content = self.make_request_get("channels")
        soup = bs4.BeautifulSoup(content, 'html5lib')
        channels = soup.body.find('div', id='footer')
        if channels:
            site_lists = channels.find_all('div', attrs={'class': 'site-list'})
            for site_list_ in site_lists:
                for site_ in site_list_.find_all('a'):
                    short_name = site_.attrs.get('href', '')
                    if short_name.startswith('/channel/'):
                        short_name = short_name.rsplit('/', 1)[-1]
                        if KinkComSite.objects.filter(short_name=short_name).exists():
                            continue
                        channel_ = site_.text.strip()
                        site = KinkComSite(short_name=short_name, name=channel_)
                        site.save()

    def get_site(self, short_name):
        content = self.make_request_get("channel/{}".format(short_name))
        soup = bs4.BeautifulSoup(content, 'html5lib')
        title_ = soup.title.text.split('-')
        if len(title_) == 3:
            name_ = title_[-2].strip()
            return KinkComSite(name=name_, short_name=short_name)

    def get_newest_shoot(self):
        now = KinkComShoot.objects.count()
        content = self.make_request_get("shoots/latest")
        if content:
            soup = bs4.BeautifulSoup(content, 'html5lib')
            shoot_list = soup.find('div', attrs={'class': 'shoot-list'})
            if shoot_list:
                shoots = shoot_list.find_all('div', attrs={'class': 'shoot'})
                latest = []
                for s in shoots:
                    try:
                        href = s.a.attrs['href']
                        latest.append(int(href.rsplit('/', 1)[-1]))
                    except (AttributeError, ValueError):
                        continue
                return max(latest)

    def get_shoot(self, shootid):
        content = self.make_request_get("shoot/{}".format(shootid))
        if content:
            _bs = bs4.BeautifulSoup(content, "html5lib")
            if not _bs.title.text:
                logging.debug('404! No shoot with id {}'.format(shootid))
                shoot = KinkComShoot(shootid=shootid)
                shoot.save()
                return shoot

            info = _bs.body.find('div', attrs={'class': 'shoot-info'})
            if not info:
                logging.error('Could not parse website!')
                return None

            shoot = KinkComShoot(shootid=shootid, exists=True)

            # Parse KinkComSite
            try:
                site_logo_ = _bs.body.find('div', attrs={"class": "column shoot-logo"})
                site_link_ = site_logo_.a.attrs.get('href', '')
                short_name = site_link_.rsplit('/', 1)[-1]
                try:
                    site = KinkComSite.objects.get(short_name=short_name)
                except ObjectDoesNotExist:
                    site = self.get_site(short_name)
                    if site is not None:
                        site.save()
            except Exception as e:
                logging.warning('Could not parse site, exception was: {}'.format(e))
                logging.warning(_bs.body)
                site = None
            shoot.site = site

            # Parse Title
            try:
                title_ = info.find(attrs={'class', 'shoot-title'})
                title = title_.renderContents().decode().replace('<br/>', ' - ').replace('  ', ' ')
            except Exception as e:
                logging.warning('Could not parse title, exception was: {}'.format(e))
                title = None
            shoot.title = title

            # Parse KinkComPerformers
            performers = []
            try:
                performers_ = info.find(attrs={'class': 'starring'})
                for perf_ in performers_.find_all('a'):
                    id_ = int(perf_.attrs.get('href', '').rsplit('/', 1)[-1])
                    try:
                        performer = KinkComPerformer.objects.get(number=id_)
                    except ObjectDoesNotExist:
                        performer = self.get_performer(id_)
                        if performer is not None:
                            performer.save()
                    performers.append(performer)
            except Exception as e:
                logging.warning('Could not parse performers, exception was: {}'.format(e))

            # Parse Date
            try:
                date_ = info.p
                date_ = date_.text.split(':')[-1].strip()
                date = datetime.datetime.strptime(date_, '%B %d, %Y').date()
            except Exception as e:
                logging.warning('Could not parse date, exception was: {}'.format(e))
                date = None
            shoot.date = date

            if site is None or title is None or date is None or None in performers:
                logging.error('Malformed Shoot, not saving!')
            else:
                shoot.save()
                for perf in performers:
                    shoot.performers.add(perf)
                logging.debug('Finished getting shoot "{}"'.format(shoot))

            return shoot
        else:
            logging.error('Could not connect to site')


if __name__ == '__name__':
    logging.basicConfig(format='%(funcName)s: %(message)s',
                        level=logging.DEBUG)
    crawler = KinkComCrawler()
    crawler.update_sites()
    print(crawler.get_shoot(9000))
