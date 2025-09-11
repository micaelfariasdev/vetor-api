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
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class PontoApiViewSet(ModelViewSet):
    queryset = Ponto.objects.all()
    serializer_class = PontoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['colaborador']
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=False, methods=["post"], url_path="salvar-registros")
    def salvar_registros(self, request):
        data = request.data
        pontos = data['registros']
        colaborador_id = data['colaborador_id']
        ano = int(data['ano'])

        resultados = []

        for idx, ponto in enumerate(pontos):
            try:
                if int(data['mes']) == 1 and int(ponto['mes']) == 12:
                    dia = date(ano-1, int(ponto['mes']), int(ponto['data']))
                else:
                    dia = date(ano, int(ponto['mes']), int(ponto['data']))

                horarios = ponto["valores"]
                feriado = True if horarios[4] else False
                atestado = True if horarios[5] else False
                delete = True if horarios[6] else False
                falta = True if horarios[7] else False
                ferias = True if horarios[8] else False

                ponto_existe = Ponto.objects.filter(
                    colaborador_id=colaborador_id,
                    data=dia
                ).first()

                if delete:
                    if ponto_existe:
                        ponto_existe.delete()
                        resultados.append(
                            {"status": "deletado", "registro": ponto})
                    continue  # <--- CORREÇÃO: Pula para o próximo item do loop

                if any(horarios[:4]):
                    entrada_manha = time.fromisoformat(
                        horarios[0]) if horarios[0] else None
                    saida_manha = time.fromisoformat(
                        horarios[1]) if horarios[1] else None
                    entrada_tarde = time.fromisoformat(
                        horarios[2]) if horarios[2] else None
                    saida_tarde = time.fromisoformat(
                        horarios[3]) if horarios[3] else None
                    dados = {
                        "colaborador": colaborador_id,
                        "data": dia,
                        "feriado": feriado,
                        "delete": delete,
                        "falta": falta,
                        "ferias": ferias,
                        "atestado": atestado,
                        "entrada_manha": entrada_manha,
                        "saida_manha": saida_manha,
                        "entrada_tarde": entrada_tarde,
                        "saida_tarde": saida_tarde,
                    }
                else:
                    dados = {
                        "colaborador": colaborador_id,
                        "data": dia,
                        "feriado": feriado,
                        "falta": falta,
                        "ferias": ferias,
                        "atestado": atestado,
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
    def mes_colaborador(self, request, pk=None):
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
        if int(mes_ponto.mes) == 1:
            ini = date(int(mes_ponto.ano) - 1, 12, 26)
            fim = date(int(mes_ponto.ano), int(mes_ponto.mes), 25)
        else:
            ini = date(int(mes_ponto.ano), int(mes_ponto.mes) - 1, 26)
            fim = date(int(mes_ponto.ano), int(mes_ponto.mes), 25)

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
                "ferias",
                "falta",
                "atestado",
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
                        "data": str(r["data"]),
                        "feriado": str(r["feriado"]),
                        "falta": str(r["falta"]),
                        "ferias": str(r["ferias"]),
                        "atestado": str(r["atestado"]),
                        "entrada_manha": str(r["entrada_manha"]) if not r["entrada_manha"] == None else None,
                        "saida_manha": str(r["saida_manha"]) if not r["saida_manha"] == None else None,
                        "entrada_tarde": str(r["entrada_tarde"]) if not r["entrada_tarde"] == None else None,
                        "saida_tarde": str(r["saida_tarde"]) if not r["saida_tarde"] == None else None,
                        "horas_trabalhadas": str(r["horas_trabalhadas"]),
                    } for r in registros_list
                ]
            })

        pdf = requests.post(
            'http://64.181.171.161/gerar-pdf', json=resultado)

        return HttpResponse(pdf, content_type="application/pdf")

    except MesPonto.DoesNotExist:
        return HttpResponse("Mês de ponto não encontrado.", status=404)
    except Exception as e:
        return HttpResponse(f"Erro ao gerar o PDF: {str(e)}", status=500)
