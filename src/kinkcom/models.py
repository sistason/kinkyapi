from django.db import models
import datetime
import logging
from bs4.element import Tag


class KinkComTag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def serialize(self):
        return {'name': self.name}


class KinkComPerformer(models.Model):
    MODEL_DATA = ["public_hair", "twitter", "ethnicity", "body_type", "hair_color", "gender", "measurements",
                  "breasts", "cup_size", "cock_girth", "cock_length", "foreskin", "height", "weight"]
    
    name = models.CharField(max_length=100)
    number = models.IntegerField()

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

    description = models.TextField(null=True)
    tags = models.ManyToManyField(KinkComTag)

    def fill_model_data(self, model_data):
        logging.debug('Filling performers "{}" data ...'.format(self.name))

        if model_data is not None and type(model_data) == Tag:
            m_data = {}
            for tr in model_data.find_all('tr'):
                try:
                    type_ = tr.td.text.strip()[:-1].lower()
                    value_ = tr.td.find_next().text.strip().lower()
                    m_data[type_] = value_
                except AttributeError:
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
    
    def serialize(self):
        serialize_ = {'name': self.name, 'number': self.number, 'tags': [i.serialize() for i in self.tags.all()],
                      'description': self.description}
        for data_ in self.MODEL_DATA:
            value_ = getattr(self, data_, None)
            if value_ is not None:
                serialize_[data_] = value_
        return serialize_

    class Meta:
        app_label = 'kinkcom'


class KinkComSite(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=50)
    is_partner = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def serialize(self):
        return {'name': self.name, 'short_name': self.short_name, 'partner': self.is_partner}

    class Meta:
        app_label = 'kinkcom'


class KinkComShoot(models.Model):
    shootid = models.IntegerField()
    title = models.CharField(max_length=500, default='')
    date = models.DateField(default=datetime.date(1970, 1, 1))

    performers = models.ManyToManyField(KinkComPerformer)
    site = models.ForeignKey(KinkComSite, null=True, on_delete=models.SET_NULL)
    tags = models.ManyToManyField(KinkComTag)
    description = models.TextField(null=True)

    exists = models.BooleanField(default=False)

    def is_complete(self):
        return bool(self.title) and bool(self.site) and self.date.strftime("%s") > 0 and self.shootid > 0

    def __str__(self):
        if not self.exists:
            return "{}: 404".format(self.shootid)

        return '{site} - {date} - {title} [{perfs}] ({id})'.format(
            site=self.site.name if self.site else '<None>',
            date=self.date,
            title=self.title,
            perfs=', '.join([str(i['name']) for i in self.performers.values('name')]),
            id=self.shootid)

    def serialize(self):
        if not self.exists:
            return {'shootid': self.shootid, 'exists': self.exists}
        return {'performers': [i.serialize() for i in self.performers.all()], 'date': self.date.strftime('%s'),
                'site': self.site.serialize() if self.site else None, 'shootid': self.shootid, 'title': self.title,
                'tags': [i.serialize() for i in self.tags.all()], 'description': self.description, 'exists': self.exists}

    class Meta:
        app_label = 'kinkcom'
