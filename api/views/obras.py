from rest_framework.viewsets import ModelViewSet
from ..serializer import ObrasSerializer, ServicosSerializer, ServicosUnidadeSerializer, UnidadeSerializer
from engenharia.models import Obras, Servicos, ServicoUnidade, Unidade


class ObrasApiViewSet(ModelViewSet):
    queryset = Obras.objects.all()
    serializer_class = ObrasSerializer

class ServicosApiViewSet(ModelViewSet):
    queryset = Servicos.objects.all()
    serializer_class = ServicosSerializer

class UnidadeApiViewSet(ModelViewSet):
    queryset = Unidade.objects.all()
    serializer_class = UnidadeSerializer

class ServicosUnidadeApiViewSet(ModelViewSet):
    queryset = ServicoUnidade.objects.all()
    serializer_class = ServicosUnidadeSerializer
