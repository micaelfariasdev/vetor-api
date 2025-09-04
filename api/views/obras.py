from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from ..serializer import ObrasSerializer, ServicosSerializer, ServicosUnidadeSerializer, UnidadeSerializer, AndarSerializer
from engenharia.models import Obras, Servicos, ServicoUnidade, Unidade, Andar
from rest_framework.response import Response
from rest_framework.decorators import action


class ObrasApiViewSet(ModelViewSet):
    queryset = Obras.objects.all()
    serializer_class = ObrasSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        servicos_ids = request.data.pop('servicos', None)

        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if servicos_ids is not None:
            try:
                instance.servicos.set(servicos_ids)
            except Exception as e:
                return Response({"servicos": f"Erro ao atualizar serviços: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(instance)
        dic = serializer.data
        if dic['tipo_obra'] == 'PREDIO':
            dic.pop("unidades")

        else:
            dic.pop("andares")

        return Response(dic)


class ServicosApiViewSet(ModelViewSet):
    queryset = Servicos.objects.all()
    serializer_class = ServicosSerializer


class UnidadeApiViewSet(ModelViewSet):
    queryset = Unidade.objects.all()
    serializer_class = UnidadeSerializer


class ServicosUnidadeApiViewSet(ModelViewSet):
    queryset = ServicoUnidade.objects.all()
    serializer_class = ServicosUnidadeSerializer

    @action(detail=False, methods=["post"], url_path="salvar-servicos")
    def salvar_servicos(self, request):
        data = request.data

        for s, v in data.items():
            try:
                ponto_existe = self.queryset.filter(
                    servico=s,
                    unidade=v['unidade']
                ).first()

                dados = {
                    'progresso': v['valor'],
                    'unidade': v['unidade'],
                    'servico': s,
                }

                if ponto_existe:
                    serializer = self.get_serializer(
                        ponto_existe, data=dados, partial=True)
                else:

                    serializer = self.get_serializer(data=dados)

                serializer.is_valid(raise_exception=True)
                serializer.save()

            except Exception as e:
                print(f"Erro no registro {s}: {e}")

                return Response({
                    "erro_no_registro": s,
                    "registro": v,
                    "detalhes": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({'succes': 'Unidades criadas/editadas com sucesso'}, status=status.HTTP_200_OK)


class AndarApiViewSet(ModelViewSet):
    queryset = Andar.objects.all()
    serializer_class = AndarSerializer
