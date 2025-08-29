from .utils import ajustar_cronograma_em_lote, gerar_pdf_ponto
from rest_framework.decorators import api_view, action
from django.shortcuts import get_object_or_404
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from .serializer import *
from engenharia.models import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from datetime import datetime, date, time
from itertools import groupby
from operator import itemgetter
from django.http import HttpResponse


class DespesasMesApiViewSet(ModelViewSet):
    queryset = DespesasMes.objects.all()
    serializer_class = DespesasMesSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not request.data.get('author'):
            data['author'] = request.user.id
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)


class DespesasItemApiViewSet(ModelViewSet):
    queryset = DespesasItem.objects.all()
    serializer_class = DespesasItemSerializer

    def partial_update(self, request, *args, **kwargs):
        despesas_mes = request.POST.get('Object')
        att = DespesasMes.objects.get(id=despesas_mes)
        att.atualizado_em = datetime.now()
        att.save()
        return super().partial_update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)


class ExcelToItensDespesas(APIView):
    serializer_class = DespesasItemSerializer

    def post(self, request, *args, **kwargs):
        despesas_mes = request.POST.get('Object')

        despesas_clear = DespesasItem.objects.filter(
            despesas_mes=despesas_mes).all()
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "Porfavor, envie o arquivo correto"}, status=status.HTTP_400_BAD_REQUEST)
        for despesas in despesas_clear:
            despesas.delete()

        import pandas as pd
        import numpy as np

        df = pd.read_excel(file, sheet_name=0, header=None)
        df.columns = df.iloc[1]
        df = df[2:]
        df = df.drop(columns=[col for col in df.columns if pd.isna(col)])
        df.drop(['Obra', 'Unidade construtiva', 'Célula construtiva', 'Etapa',
                'Subetapa', 'Serviço', 'Data da baixa', 'Or', 'Valor'], axis=1, inplace=True)
        df["Valor do documento"] = pd.to_numeric(
            df["Valor do documento"], errors="coerce").round(2)
        df.sort_values('Credor/Histórico', inplace=True)
        df.drop_duplicates(subset='Título/Parcela', inplace=True)
        df = df.replace({np.nan: ' '})
        df = df.rename(columns={
            'Data': 'data',
            'Documento': 'documento',
            'Título/Parcela': 'titulo',
            'Credor/Histórico': 'empresa',
            'Valor do documento': 'valor',
            'Observação': 'descricao'
        })
        df['data'] = pd.to_datetime(df['data'], dayfirst=True).dt.date
        try:
            for _, row in df.iterrows():
                data = row.to_dict()
                data['despesas_mes'] = despesas_mes

                serializer = self.serializer_class(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    print(serializer.errors)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        att = DespesasMes.objects.get(id=despesas_mes)
        att.atualizado_em = datetime.now()
        att.save()
        return Response({"message": "Arquivo processado com sucesso"}, status=status.HTTP_200_OK)


class ObrasApiViewSet(ModelViewSet):
    queryset = Obras.objects.all()
    serializer_class = ObrasSerializer


class CronogramasApiViewSet(ModelViewSet):
    queryset = Cronograma.objects.all()
    serializer_class = CronogramaSerializer


class ColaboradorApiViewSet(ModelViewSet):
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'


class PontoApiViewSet(ModelViewSet):
    queryset = Ponto.objects.all()
    serializer_class = PontoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['colaborador']

    @action(detail=False, methods=["post"], url_path="salvar-registros")
    def salvar_registros(self, request):
        data = request.data
        pontos = data['registros']
        colaborador_id = data['colaborador_id']
        ano = int(data['ano'])
        mes = int(data['mes'])

        resultados = []

        for idx, ponto in enumerate(pontos):
            try:
                dia = date(ano, mes, int(ponto['data']))
                horarios = ponto["valores"]
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


class ServicosCronogramasApiViewSet(ModelViewSet):
    queryset = ServicoCronograma.objects.all()
    serializer_class = ServicoCronogramaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cronograma']


class XMLToCronograma(APIView):
    serializer_class = ServicoCronogramaSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        cronograma_id = request.POST.get('cronograma')
        cronograma_obj = get_object_or_404(Cronograma, id=cronograma_id)
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "Por favor, envie o arquivo XML correto"}, status=status.HTTP_400_BAD_REQUEST)

        ServicoCronograma.objects.filter(cronograma=cronograma_obj).delete()

        import xml.etree.ElementTree as ET
        tree = ET.parse(file)
        root = tree.getroot()
        ns = {'p': 'http://schemas.microsoft.com/project'}

        u_lvl1 = None
        u_lvl2 = None
        u_lvl3 = None

        for task in root.findall('p:Tasks/p:Task', ns):
            predecessors = []
            nome = task.find('p:Name', ns)
            uid = task.find('p:UID', ns)
            inicio = task.find('p:Start', ns)
            fim = task.find('p:Finish', ns)
            nivel = task.find('p:OutlineLevel', ns)
            intnivel = int(nivel.text)
            for pred in task.findall('p:PredecessorLink', ns):
                pred_uid = pred.find('p:PredecessorUID', ns)
                if pred_uid is not None:
                    predecessors.append(int(pred_uid.text))

            if intnivel == 0:
                continue

            if intnivel == 1:
                pai = None
            elif intnivel == 2:
                pai = u_lvl1
            elif intnivel == 3:
                pai = u_lvl2
            elif intnivel == 4:
                pai = u_lvl3
            else:
                pai = None

            inicio_str = inicio.text if inicio is not None else None
            fim_str = fim.text if fim is not None else None

            data_inicio = datetime.strptime(inicio_str.split(
                'T')[0], '%Y-%m-%d').date() if inicio_str else None
            data_fim = datetime.strptime(fim_str.split(
                'T')[0], '%Y-%m-%d').date() if fim_str else None

            dias = (data_fim - data_inicio).days if data_inicio and data_fim else 0

            data = {
                'cronograma': cronograma_obj.id,
                'pai': pai.id if pai else None,
                'uid': int(uid.text),
                'titulo': nome.text if nome is not None else '',
                'inicio': data_inicio,
                'fim': data_fim,
                'dias': dias,
                'nivel': intnivel,
            }

            predecessores_objs = []
            for x in predecessors:
                if x is not None and x > 0:
                    pred = ServicoCronograma.objects.filter(uid=x).first()
                    if pred:
                        predecessores_objs.append(pred)

            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                obj = serializer.save()
                obj.predecessores.set(predecessores_objs)

                if intnivel == 1:
                    u_lvl1 = obj
                elif intnivel == 2:
                    u_lvl2 = obj
                elif intnivel == 3:
                    u_lvl3 = obj
            else:
                print(serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Cronograma importado com sucesso"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def recalcular_cronograma(request, cronograma_id):
    cronograma = get_object_or_404(Cronograma, id=cronograma_id)
    ajustar_cronograma_em_lote(cronograma)
    return Response({"status": "cronograma atualizado"})


@api_view(['GET'])
def pdf_pontos_relatorio(request, mes_id):
    Mes = MesPonto.objects.get(id=mes_id)
    pontos = Ponto.objects.filter(
        data__year=Mes.ano,
        data__month=Mes.mes,
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
