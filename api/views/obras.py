from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from ..serializer import ObrasSerializer, ServicosSerializer, ServicosUnidadeSerializer, UnidadeSerializer, AndarSerializer
from engenharia.models import Obras, Servicos, ServicoUnidade, Unidade, Andar
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class ObrasApiViewSet(ModelViewSet):
    queryset = Obras.objects.all()
    serializer_class = ObrasSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=True, methods=["post"], url_path="add-servicos")
    def add_servicos(self, request, pk=None):
        obra = self.get_object()
        servico_id = request.data.get("servico_id")
        if servico_id:
            obra.servicos.add(servico_id)
            obra.save()
            return Response({"status": "serviço adicionado"})
        return Response({"error": "servico_id não enviado"}, status=400)

    @action(detail=True, methods=["delete"], url_path="remove-servicos")
    def remove_servicos(self, request, pk=None):
        obra = self.get_object()
        servico_id = request.data.get("servico_id")
        if servico_id:
            obra.servicos.remove(servico_id)
            return Response({"status": "serviço removido"})
        return Response({"error": "servico_id não enviado"}, status=400)

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

    @action(detail=True, methods=["GET"], url_path="servicos")
    def servicos(self, request, pk=None):
        instance = self.get_object()

        servicosUnidades_queryset = ServicoUnidade.objects.filter(
            unidade__obra=instance
        )

        serializerservicosUnidades = ServicosUnidadeSerializer(
            servicosUnidades_queryset, many=True
        )
        servicos_unidades_data = serializerservicosUnidades.data

        servicos_mapa = {}
        for item in servicos_unidades_data:
            unidade_id = item["unidade"]
            servico_nome = item["servico"]
            progresso = item["progresso"]

            if unidade_id not in servicos_mapa:
                servicos_mapa[unidade_id] = []

            servicos_mapa[unidade_id].append(
                {
                    "servico": servico_nome,
                    "progresso": progresso,
                }
            )

        serializer_instance = self.get_serializer(instance)
        dic = serializer_instance.data

        for andar in dic["andares"]:
            if 'unidades' not in andar:
                continue 

            for unidade in andar["unidades"]:
                unidade_id = unidade["id"]

                unidade["servicos"] = []

                if unidade_id in servicos_mapa:
                    unidade["servicos"] = servicos_mapa[unidade_id]

        return Response(dic)

class ServicosApiViewSet(ModelViewSet):
    queryset = Servicos.objects.all()
    serializer_class = ServicosSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class UnidadeApiViewSet(ModelViewSet):
    queryset = Unidade.objects.all()
    serializer_class = UnidadeSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class ServicosUnidadeApiViewSet(ModelViewSet):
    queryset = ServicoUnidade.objects.all()
    serializer_class = ServicosUnidadeSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=False, methods=["post"], url_path="get-servicos")
    def get_servicos(self, request):
        data = request.data

        unidade_id = data.get('unidade_id')

        if not unidade_id:
            return Response(
                {"detail": "O ID de unidade é obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            servicos_unidade = ServicoUnidade.objects.filter(
                unidade_id=unidade_id
            )

            serializer = self.get_serializer(servicos_unidade, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"Ocorreu um erro ao processar a requisição: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="get-servicos-detail")
    def get_servicos(self, request):
        serv = request.data.get("serv")
        if not serv:
            return Response({"detail": "Parâmetro 'serv' é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            servicos_unidade = ServicoUnidade.objects.filter(servico=serv)
            serializer = self.get_serializer(servicos_unidade, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Ocorreu um erro ao processar a requisição: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
