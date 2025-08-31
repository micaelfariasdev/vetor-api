from rest_framework.viewsets import ModelViewSet
from ..serializer import ObrasSerializer, ServicosSerializer, ServicosUnidadeSerializer, UnidadeSerializer, AndarSerializer
from engenharia.models import Obras, Servicos, ServicoUnidade, Unidade, Andar


class ObrasApiViewSet(ModelViewSet):
    queryset = Obras.objects.all()
    serializer_class = ObrasSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        servicos_ids = request.data.pop('servicos', None)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if servicos_ids is not None:
            try:
                instance.servicos.set(servicos_ids)
            except Exception as e:
                return Response({"servicos": f"Erro ao atualizar serviços: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data)


class ServicosApiViewSet(ModelViewSet):
    queryset = Servicos.objects.all()
    serializer_class = ServicosSerializer

class UnidadeApiViewSet(ModelViewSet):
    queryset = Unidade.objects.all()
    serializer_class = UnidadeSerializer

class ServicosUnidadeApiViewSet(ModelViewSet):
    queryset = ServicoUnidade.objects.all()
    serializer_class = ServicosUnidadeSerializer

class AndarApiViewSet(ModelViewSet):
    queryset = Andar.objects.all()
    serializer_class = AndarSerializer
