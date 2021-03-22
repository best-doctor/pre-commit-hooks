from django.db import models


class ModelA(models.Model):
    ok_date = models.DateField()
    date_bad = models.DateField()
    ok_at = models.DateTimeField()
    bad_datetime = models.DateTimeField()
    should_be_ignored = models.CharField()
