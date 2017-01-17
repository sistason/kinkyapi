from django.db import models
import datetime
import logging
from bs4.element import Tag


class KinkComPerformer(models.Model):
    name = models.CharField(max_length=100)
    number = models.SmallIntegerField()

    scene_role = models.CharField(max_length=50, null=True)
    public_hair = models.CharField(max_length=50, null=True)
    twitter = models.CharField(max_length=50, null=True)
    ethnicity = models.CharField(max_length=50, null=True)
    body_type = models.CharField(max_length=50, null=True)
    hair_color = models.CharField(max_length=50, null=True)
    gender = models.CharField(max_length=50, null=True)
    measurements = models.CharField(max_length=50, null=True)
    breasts = models.CharField(max_length=50, null=True)
    cup_size = models.CharField(max_length=50, null=True)
    cock_girth = models.CharField(max_length=50, null=True)
    cock_length = models.CharField(max_length=50, null=True)
    foreskin = models.CharField(max_length=50, null=True)
    height = models.CharField(max_length=50, null=True)
    weight = models.CharField(max_length=50, null=True)

    def fill_model_data(self, model_data):
        logging.debug('Filling performers "{}" data ...'.format(self.name))

        if model_data is not None and type(model_data) == Tag:
            m_data = {}
            for tr in model_data.find_all('tr'):
                try:
                    type_ = tr.td.text.strip()[:-1].lower()
                    value_ = tr.td.find_next().text.strip().lower()
                    m_data[type_] = value_
                except AttributeError as e:
                    logging.debug('Unknown data: {}'.format(tr))

            self.measurements = m_data.get('measurements', None)
            self.breasts = m_data.get('breasts', None)
            self.cup_size = m_data.get('cup size', None)
            self.cock_girth = m_data.get('cock girth', None)
            self.cock_length = m_data.get('cock length', None)
            self.foreskin = m_data.get('foreskin', None)
            self.height = m_data.get('height', None)
            self.weight = m_data.get('weight', None)
            self.scene_role = m_data.get('scene role', None)
            self.pubic_hair = m_data.get('public hair', None)
            self.twitter = m_data.get('twitter', None)
            self.body_type = m_data.get('body type', None)
            self.hair_color = m_data.get('hair color', None)
            self.gender = m_data.get('gender', None)
            self.ethnicity = m_data.get('ethnicity', None)

    def __str__(self):
        return "{}: {}".format(self.number, self.name)


class KinkComSite(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class KinkComShoot(models.Model):
    performers = models.ManyToManyField(KinkComPerformer)
    date = models.DateField(default=datetime.date(1970,1,1))
    site = models.ForeignKey(KinkComSite, null=True)
    shootid = models.SmallIntegerField()
    title = models.CharField(max_length=500, default='')
    exists = models.BooleanField(default=False)

    def is_complete(self):
        return bool(self.title) and bool(self.site) and self.date.strftime("%s") > 0 and self.shootid > 0

    def __str__(self):
        if not self.exists:
            return "404"

        return '{site} - {date} - {title} [{perfs}] ({id})'.format(

            site=self.site.name,
            date=self.date,
            title=self.title,
            perfs=', '.join([str(i['name']) for i in self.performers.values('name')]),
            id=self.shootid)
