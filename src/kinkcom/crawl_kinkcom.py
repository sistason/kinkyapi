#!/usr/bin/env python3

import requests
import logging
import bs4
import datetime

from django.core.exceptions import ObjectDoesNotExist
from kinkcom.models import KinkComSite, KinkComShoot, KinkComPerformer, KinkComTag


logging.basicConfig(format='%(funcName)s: %(message)s', level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class KinkComCrawler:
    name = 'Kink.com'
    kink_url = 'https://www.kink.com/'

    def __init__(self):
        self._cookies = None
        self._headers = None
        self._session = requests.Session()

        self._set_headers()
        self._set_cookies()

    def _set_headers(self):
        # TODO: randomized user-agent
        self._headers = {'Accept-Language': 'en-US,en;q=0.5'}

    def _set_cookies(self):
        self._make_request_get("")
        self._session.cookies['viewing-preferences'] = 'straight,gay'

    def _make_request_get(self, url, data=None):
        retries = 3
        while retries > 0:
            try:
                return self._session.get(self.kink_url + url, data=data,
                                         cookies=self._cookies, headers=self._headers, timeout=2)
            except requests.Timeout:
                retries -= 1
            except Exception as e:
                logging.debug('Caught Exception "{}" while making a get-request to "{}"'.format(e, url))
                break

    def update_shoots(self):
        all_shoots = KinkComShoot.objects.all()
        end = self.get_newest_shoot()
        for i in range(end):
            logger.info('Updating shoot {}/{}'.format(i, end))
            if all_shoots.filter(shootid=i).exists():
                logger.info('\tShoot already exists')
                continue
            self.get_shoot(i)

    def get_performer(self, id_, force=False):
        if not force:
            perf = KinkComPerformer.objects.filter(number=id_)
            if perf.exists():
                return perf.get()

        response = self._make_request_get("model/{}".format(id_))
        if response is None:
            logger.error("Could not get model {id_}!")
            return

        if response.url == self.kink_url:
            logger.warning('404! No performer with id {}'.format(id_))
            return

        _bs = bs4.BeautifulSoup(response.text, "lxml")
        container = _bs.body.find("div", attrs={'class': "biography-container"})
        page_title_ = container.find("h1", attrs={'class': "page-title"})
        name_ = page_title_.find("span", attrs={'class': "favorite-button"}).attrs.get("data-title")

        performer, _ = KinkComPerformer.objects.get_or_create(name=name_, number=id_)
        for tag in container.find("div", attrs={'class': "bio-tags"}).find_all("a"):
            tag_, _ = KinkComTag.objects.get_or_create(name=tag.span.text)
            performer.tags.add(tag_)

        data_ = container.find('table', attrs={'class': "model-data"})
        performer.fill_model_data(model_data=data_)

        bio = container.find("p", attrs={'class': "bio"})
        if bio:
            performer.description = bio.span.text

        return performer

    def update_sites(self):
        response = self._make_request_get("channels")
        if response is None:
            logger.error("Could not get channels!")
            return

        soup = bs4.BeautifulSoup(response.text, 'lxml')
        channels = soup.body.find('div', id='footer')
        if channels:
            site_lists = channels.find_all('div', attrs={'class': 'site-list'})
            for site_list_ in site_lists:
                for site_ in site_list_.find_all('a'):
                    short_name = site_.attrs.get('href', '')
                    if short_name.startswith('/channel/'):
                        short_name = short_name.rsplit('/', 1)[-1]
                        channel_ = site_.text.strip()
                        site, _ = KinkComSite.objects.get_or_create(short_name=short_name)
                        site.name = channel_
                        site.save()

    def get_newest_shoot(self):
        now = KinkComShoot.objects.count()
        response = self._make_request_get("shoots/latest")
        if response is None:
            logger.error('Could not get /latest')
            return

        soup = bs4.BeautifulSoup(response.text, 'lxml')
        shoot_list = soup.find('div', attrs={'class': 'shoots-grid-4x5'})
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
        response = self._make_request_get("shoot/{}".format(shootid))
        if response is None:
            logger.error(f'Could not get shoot {shootid}')
            return

        _bs = bs4.BeautifulSoup(response.text, 'lxml')

        if response.status_code == 404:
            logger.debug('404! No shoot with id {}'.format(shootid))
            shoot = KinkComShoot(shootid=shootid)
            shoot.save()
            return shoot

        info = _bs.body.find('div', attrs={'class': 'shoot-content'})
        if not info:
            logger.error('Could not parse website!')
            return None

        shoot, _ = KinkComShoot.objects.get_or_create(shootid=shootid, exists=True)

        # Parse KinkComSite
        try:
            site_logo_ = _bs.body.find('div', attrs={"class": "column shoot-logo"})
            name_ = site_logo_.a.text.strip()
            site_link_ = site_logo_.a.attrs.get('href', '')
            short_name = site_link_.rsplit('/', 1)[-1]
            try:
                site = KinkComSite.objects.get(short_name=short_name)
            except ObjectDoesNotExist:
                site = None
                channels = _bs.body.find('div', id='footer')
                if channels:
                    site_lists = channels.find_all('div', attrs={'class': 'site-list'})
                    for site_list_ in site_lists:
                        for site_ in site_list_.find_all('a'):
                            short_name_ = site_.attrs.get('href', '')
                            if short_name_ == site_link_:
                                logger.warning("You should call update_sites before, this is inefficient otherwise")
                                short_name_ = short_name_.rsplit('/', 1)[-1]
                                channel_ = site_.text.strip()
                                site = KinkComSite(short_name=short_name_, name=channel_)
                                site.save()

                if site is None:
                    # Special Site
                    name_ = name_ if name_ else short_name.capitalize()
                    site = KinkComSite(short_name=short_name, name=name_, is_partner=True)
                    site.save()
                    logger.debug('Found special/partner site "{}"'.format(site))

            shoot.site = site
        except Exception as e:
            logger.warning('Could not parse site, exception was: {}'.format(e))

        # Parse Title
        try:
            title_ = info.find("h1", attrs={'class': "shoot-title"})
            shoot.title = title_.find("span", attrs={'class': "favorite-button"}).attrs.get("data-title")
        except Exception as e:
            logger.warning('Could not parse title, exception was: {}'.format(e))

        # Parse KinkComPerformers
        performers = []
        try:
            performers_ = info.find(attrs={'class': 'starring'})
            for perf_ in performers_.find_all('a'):
                id_ = 0
                try:
                    id_ = int(perf_.attrs.get('href', '').split('/')[2])
                    performer = self.get_performer(id_)
                    if not performer:
                        raise ValueError
                except ValueError:
                    if not perf_.text:
                        continue
                    # Since performer 404s / has no link, get name from HTML and be done with it
                    performer, _ = KinkComPerformer.objects.get_or_create(name=perf_.text, number=id_)

                performers.append(performer)

        except Exception as e:
            logger.warning('Could not parse performers, exception was: {}'.format(e))

        # Parse Date
        try:
            date_ = info.find(attrs={'class': 'shoot-date'})
            shoot.date = datetime.datetime.strptime(date_.text, '%B %d, %Y').date()
        except Exception as e:
            logger.warning('Could not parse date, exception was: {}'.format(e))

        # Parse Rating
        try:
            rating_ = info.find("div", attrs={'class': 'shoot-rating'})
            shoot.rating = int(rating_.find("div", attrs={'class': 'average-rating'}).attrs.get("data-rating"))
            print(shoot.rating)
        except (ValueError, AttributeError):
            pass

        # Parse Description
        try:
            description_ = info.find("span", attrs={'class': 'description-text'})
            shoot.description = description_.text
        except AttributeError:
            pass

        # Parse Tags
        try:
            tags_ = [KinkComTag.objects.get_or_create(name=tag.text)[0]
                     for tag in info.find("p", attrs={'class': "tag-list"}).find_all("a")]
        except AttributeError:
            tags_ = []

        if shoot.site is None or shoot.title is None or shoot.date is None:
            logger.error('Malformed Shoot, not saving!')
        else:
            shoot.save()
            for perf in performers:
                if perf is not None:
                    shoot.performers.add(perf)
            for tag in tags_:
                shoot.tags.add(tag)
            logging.debug('Finished getting shoot "{}"'.format(shoot))

        return shoot
