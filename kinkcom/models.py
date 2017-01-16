from django.db import models
import datetime


class KinkComPerformerData:
    height = models.CharField(max_length=50, null=True)
    weight = models.CharField(max_length=50, null=True)
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


class KinkComPerformerManager(models.Manager):
    def create_performer(self, name=None, number=None, model_data=None):
        model = self.create(name=name, number=number)

        if model_data is not None and getattr(model_data, "find_all", None):
            m_data = {}
            for tr in model_data.find_all('tr'):
                try:
                    type_ = tr.td.text.strip()[:-1].lower()
                    value_ = tr.td.find_next().text.strip().lower()
                    m_data[type_] = value_
                except AttributeError:
                    pass

            model.measurements = m_data.get('measurements', None)
            model.breasts = m_data.get('breasts', None)
            model.cup_size = m_data.get('cup size', None)
            model.cock_girth = m_data.get('cock girth', None)
            model.cock_length = m_data.get('cock length', None)
            model.foreskin = m_data.get('foreskin', None)
            model.height = m_data.get('height', None)
            model.weight = m_data.get('weight', None)
            model.scene_role = m_data.get('scene role', None)
            model.pubic_hair = m_data.get('public hair', None)
            model.twitter = m_data.get('twitter', None)
            model.body_type = m_data.get('body type', None)
            model.hair_color = m_data.get('hair color', None)
            model.gender = m_data.get('gender', None)
            model.ethnicity = m_data.get('ethnicity', None)

        return model


class KinkComPerformer(models.Model, KinkComPerformerData):
    name = models.CharField(max_length=100)
    number = models.SmallIntegerField()

    objects = KinkComPerformerManager()


class KinkComSite(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=50)


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
            perfs=', '.join(self.performers.values('name')),
            id=self.shootid)
