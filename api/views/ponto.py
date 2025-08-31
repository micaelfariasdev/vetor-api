from ..utils import gerar_pdf_ponto
from rest_framework.decorators import api_view, action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from ..serializer import PontoSerializer, MesPontoSerializer
from engenharia.models import Ponto, MesPonto, Colaborador
from rest_framework.response import Response
from rest_framework import status
from datetime import date, time
from itertools import groupby
from operator import itemgetter
from django.http import HttpResponse


class PontoApiViewSet(ModelViewSet):
    queryset = Ponto.objects.all()
    serializer_class = PontoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['colaborador']

    @action(detail=False, methods=["post"], url_path="salvar-registros")
    def mes_colaborador(self, request):
        data = request.data
        pontos = data['registros']
        colaborador_id = data['colaborador_id']
        ano = int(data['ano'])

        resultados = []

        for idx, ponto in enumerate(pontos):
            try:
                dia = date(ano, int(ponto['mes']), int(ponto['data']))
                horarios = ponto["valores"]
                feriado = True if horarios[4] else False
                entrada_manha = time.fromisoformat(horarios[0])
                saida_manha = time.fromisoformat(horarios[1])
                entrada_tarde = time.fromisoformat(horarios[2])
                saida_tarde = time.fromisoformat(horarios[3])

                ponto_existe = Ponto.objects.filter(
                    colaborador_id=colaborador_id,
                    data=dia
                ).first()

                dados = {
                    "colaborador": colaborador_id,
                    "data": dia,
                    "feriado": feriado,
                    "entrada_manha": entrada_manha,
                    "saida_manha": saida_manha,
                    "entrada_tarde": entrada_tarde,
                    "saida_tarde": saida_tarde,
                }

                if ponto_existe:
                    serializer = self.get_serializer(
                        ponto_existe, data=dados, partial=True)
                else:
                    serializer = self.get_serializer(data=dados)

                serializer.is_valid(raise_exception=True)
                serializer.save()
                resultados.append(serializer.data)

            except Exception as e:
                print(f"Erro no registro {idx}: {e}")

                return Response({
                    "erro_no_registro": idx,
                    "registro": ponto,
                    "detalhes": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(resultados, status=status.HTTP_200_OK)


class MesPontoApiViewSet(ModelViewSet):
    queryset = MesPonto.objects.all()
    serializer_class = MesPontoSerializer

    @action(detail=True, methods=["get"], url_path="relacao")
    def salvar_registros(self, request, pk=None):
        mes_ponto = self.get_object()
        obra = mes_ponto.obra
        colaboradores = obra.colaboradores.all()

        data = {
            'dados': MesPontoSerializer(mes_ponto).data,
            'funcionarios': list(colaboradores.values())
        }
        return Response(data)


@api_view(['GET'])
def pdf_pontos_relatorio(request, mes_id):
    """
    Gera um relatório em PDF com os pontos de todos os colaboradores
    de um mês e obra específicos.
    """
    try:
        mes_ponto = MesPonto.objects.get(id=mes_id)
        
        ini = date(int(mes_ponto.ano), int(mes_ponto.mes), 1) # Exemplo: 1º dia do mês
        fim = date(int(mes_ponto.ano), int(mes_ponto.mes), 28) # Exemplo: 28º dia do mês

        pontos = Ponto.objects.filter(
            data__range=(ini, fim),
            colaborador__obra=mes_ponto.obra
        ).select_related("colaborador").order_by("colaborador__nome", "data")

        data = list(
            pontos.values(
                "id",
                "colaborador__id",
                "colaborador__nome",
                "colaborador__cargo",
                "colaborador__obra__nome",
                "data",
                "feriado",
                "entrada_manha",
                "saida_manha",
                "entrada_tarde",
                "saida_tarde",
                "horas_trabalhadas",
            )
        )

        resultado = []
        for _, registros in groupby(data, key=itemgetter("colaborador__id")):
            registros_list = list(registros)
            resultado.append({
                "colaborador": registros_list[0]['colaborador__nome'],
                "cargo": registros_list[0]['colaborador__cargo'],
                "obra": registros_list[0]['colaborador__obra__nome'],
                "mes": int(mes_ponto.mes),
                "ano": int(mes_ponto.ano),
                "pontos": [
                    {
                        "data": r["data"],
                        "feriado": str(r["feriado"]),
                        "entrada_manha": r["entrada_manha"],
                        "saida_manha": r["saida_manha"],
                        "entrada_tarde": r["entrada_tarde"],
                        "saida_tarde": r["saida_tarde"],
                        "horas_trabalhadas": r["horas_trabalhadas"],
                    } for r in registros_list
                ]
            })

        pdf = gerar_pdf_ponto(resultado)
        
        return HttpResponse(pdf, content_type="application/pdf")
        
    except MesPonto.DoesNotExist:
        return HttpResponse("Mês de ponto não encontrado.", status=404)
    except Exception as e:
        return HttpResponse(f"Erro ao gerar o PDF: {str(e)}", status=500)

