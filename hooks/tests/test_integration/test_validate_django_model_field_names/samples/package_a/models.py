from django.db import models
from django.db.models import CharField, DateField, DateTimeField, Model


class MyDateTimeExtraField(DateTimeField):
    pass


class ModelA(models.Model):
    ok_date = models.DateField()
    date_bad = models.DateField()
    ok_at = models.DateTimeField()
    bad_datetime = models.DateTimeField()
    should_be_ignored = models.CharField()


class ModelB(Model):
    ok_date = DateField()
    date_bad = DateField()
    ok_at = DateTimeField()
    bad_datetime = DateTimeField()
    my_ok_at = MyDateTimeExtraField()
    my_bad_datetime = MyDateTimeExtraField()
    should_be_ignored = CharField()
