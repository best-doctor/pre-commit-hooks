from __future__ import annotations

from django.db import models


class Model(models.Model):

    field1 = models.CharField(
        'Field 1', null=True, blank=True, max_length=255
    )
    field2 = models.CharField(
        'Field 2', null=True, blank=True, max_length=255
    )  # deprecated TICKET-123 16.11.2021, use field1 instead
