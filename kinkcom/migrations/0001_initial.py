# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-15 16:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Performer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('number', models.SmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Shoot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('shootid', models.SmallIntegerField()),
                ('title', models.CharField(max_length=500)),
                ('performers', models.ManyToManyField(to='kinkcom.Performer')),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='shoot',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kinkcom.Site'),
        ),
    ]