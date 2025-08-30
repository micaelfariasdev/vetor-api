from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from ..serializer import ColaboradorSerializer
from engenharia.models import Colaborador
from rest_framework.decorators import action
from rest_framework.response import Response


class ColaboradorApiViewSet(ModelViewSet):
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'

    @action(detail=True, methods=["get"], url_path="pontos")
    def salvar_registros(self, request, pk=None):
        colaborador = self.get_object()
        pontos = colaborador.pontos.all()

        data = {
            'dados': self.serializer_class(colaborador).data,
            'pontos': list(pontos.values())
        }
        return Response(data)
