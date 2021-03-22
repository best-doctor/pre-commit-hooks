from django.db.models import CharField, DateField, DateTimeField, Model


class ModelB(Model):
    ok_date = DateField()
    date_bad = DateField()
    ok_at = DateTimeField()
    bad_datetime = DateTimeField()
    should_be_ignored = CharField()
