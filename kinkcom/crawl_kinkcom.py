#!/usr/bin/env python3

import requests
import logging
import bs4
import datetime

from django.core.exceptions import ObjectDoesNotExist
from kinkcom.models import Site, Shoot, Performer


class KinkyCrawler:

    def __init__(self):
        self._cookies = None

        self.set_headers()

    def set_headers(self):
        # TODO: randomized user-agent
        self._headers = {'Accept-Language': 'en-US,en;q=0.5'}

    def set_cookies(self):
        return NotImplementedError

    def get_shoot(self, shootid):
        return NotImplementedError

    def get_newest_shoot(self):
        return NotImplementedError

    def update_shoots(self):
        all_shoots = Shoot.object.all()
        end = self.get_newest_shoot()
        for i in range(end):
            if all_shoots.filter(shootid=i).exists():
                continue
            self.get_shoot(i)

    def make_request_get(self, url, data=None):
        if data is None:
            data = {}
        if not self._cookies:
            self.set_cookies()
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
    shoot_url = 'https://kink.com/'

    def set_cookies(self):
        _ret = requests.get("http://www.kink.com")
        _cookies = _ret.cookies
        _cookies['viewing-preferences'] = 'straight,gay'
        self._cookies = _cookies

    def get_performer(self, id_):
        content = self.make_request_get("http://kink.com/model/{}".format(id_))
        _bs = bs4.BeautifulSoup(content, "html5lib")
        if _bs.title.text != "Error":
            name_ = _bs.title.text
            data_ = _bs.find('table', attrs={'class':"model-data"})
            print(name_, id_, data_)
            return Performer.objects.create_performer(name=name_, number=id_, model_data=data_)

        return None

    def update_sites(self):
        content = self.make_request_get("http://kink.com/channels")
        soup = bs4.BeautifulSoup(content, 'html5lib')
        channels = soup.body.find('div', id='footer')
        if channels:
            site_lists = channels.find_all('div', attrs={'class': 'site-list'})
            for site_list_ in site_lists:
                for site_ in site_list_.find_all('a'):
                    short_name = site_.attrs.get('href','')
                    if short_name.startswith('/channel/'):
                        short_name = short_name.rsplit('/', 1)[-1]
                        if Site.objects.filter(short_name=short_name).exists():
                            continue
                        channel_ = site_.text.strip()
                        site = Site(short_name=short_name, name=channel_)
                        site.save()

    def get_site(self, short_name):
        content = self.make_request_get("http://kink.com/channel/{}".format(short_name))
        soup = bs4.BeautifulSoup(content, 'html5lib')
        title_ = soup.title.text.split('-')
        if len(title_) == 3:
            name_ = title_[-2].strip()
            return Site(name=name_, short_name=short_name)

    def get_newest_shoot(self):
        content = self.make_request_get("http://kink.com/shoots/latest")
        if content:
            soup = bs4.BeautifulSoup(content, 'html5lib')
            shoot_list = soup.find('div', attrs={'class':'shoot-list'})
            if shoot_list:
                shoots = shoot_list.find_all('div', attrs={'class':'shoot'})
                latest = []
                for s in shoots:
                    try:
                        href = s.a.attrs['href']
                        latest.append(int(href.rsplit('/', 1)[-1]))
                    except (AttributeError, ValueError):
                        continue
                return max(latest)

    def get_shoot(self, shootid):
        content = self.make_request_get("http://kink.com/shoot/{}".format(shootid))
        if content:
            _bs = bs4.BeautifulSoup(content, "html5lib")
            if not _bs.title.text:
                logging.debug('404! No shoot with id {}'.format(shootid))
                shoot = Shoot(shootid=shootid)
                shoot.save()
                return shoot

            info = _bs.body.find('div', attrs={'class': 'shoot-info'})
            if not info:
                logging.error('Could not parse website!')
                return None


            try:
                # Get link of the site from a.href
                site_logo_ = _bs.body.find('div', attrs={"class": "column shoot-logo"})
                site_link_ = site_logo_.a.attrs.get('href', '')
                short_name = site_link_.rsplit('/', 1)[-1]
                try:
                    site = Site.objects.get(short_name=short_name)
                except ObjectDoesNotExist:
                    site = self.get_site(short_name)
                    if site is not None:
                        site.save()
            except Exception as e:
                logging.warning('Could not parse site, exception was: {}'.format(e))
                logging.warning(_bs.body)
                site = None


            try:
                title_ = info.find(attrs={'class', 'shoot-title'})
                title = title_.renderContents().decode().replace('<br/>', ' - ').replace('  ', ' ')
            except Exception as e:
                logging.warning('Could not parse title, exception was: {}'.format(e))
                title = None

            performers = []
            try:
                performers_ = info.find(attrs={'class': 'starring'})
                for perf_ in performers_.find_all('a'):
                    id_ = int(perf_.attrs.get('href', '').rsplit('/', 1)[-1])
                    try:
                        performer = Performer.objects.get(number=id_)
                    except ObjectDoesNotExist:
                        performer = self.get_performer(id_)
                        if performer is not None:
                            performer.save()
                    performers.append(performer)
            except Exception as e:
                logging.warning('Could not parse performers, exception was: {}'.format(e))

            try:
                date_ = info.p
                date_ = date_.text.split(':')[-1].strip()
                # TODO: Check if kink.com gives out dates in local locale settings
                date = datetime.datetime.strptime(date_, '%B %d, %Y').date()
            except Exception as e:
                logging.warning('Could not parse date, exception was: {}'.format(e))
                date = None

            shoot = Shoot(shootid=shootid)
            if site is not None:
                shoot.site = site
            if title is not None:
                shoot.title = title
            if date is not None:
                shoot.date = date
            shoot.save()
            if performers is not []:
                for perf in performers:
                    shoot.performers.add(perf)
                shoot.performers.save()

            return shoot
        else:
            logging.error('Could not connect to site')


if __name__ == '__name__':
    logging.basicConfig(format='%(funcName)s: %(message)s',
                        level=logging.DEBUG)
    crawler = KinkComCrawler()
    crawler.update_sites()
    print(crawler.get_shoot(9000))