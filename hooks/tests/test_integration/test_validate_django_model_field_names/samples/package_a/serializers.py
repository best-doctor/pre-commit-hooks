from rest_framework import serializers
from rest_framework.serializers import DateTimeField, ModelSerializer

from .models import ModelA


class ShouldBeIngoredSerializer(ModelSerializer):

    class Meta:
        model = ModelA
        fields = ['id', 'dt_1', 'dt_2']

    dt_1 = DateTimeField(source='ok_at')
    dt_2 = serializers.DateTimeField(source='ok_at')
