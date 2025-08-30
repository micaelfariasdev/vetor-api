from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from ..serializer import ColaboradorSerializer
from engenharia.models import Colaborador


class ColaboradorApiViewSet(ModelViewSet):
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'
