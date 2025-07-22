from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from .serializer import DespesasMesSerializer, DespesasItemSerializer, ObrasSerializer, ServicoCronogramaSerializer, CronogramaSerializer
from engenharia.models import DespesasMes, DespesasItem, Obras, ServicoCronograma, Cronograma
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from datetime import datetime


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


class ServicosCronogramasApiViewSet(ModelViewSet):
    queryset = ServicoCronograma.objects.all()
    serializer_class = ServicoCronogramaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cronograma']


class XMLToCronograma(APIView):
    serializer_class = ServicoCronogramaSerializer

    def post(self, request, *args, **kwargs):
        cronograma = request.POST.get('cronograma')
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "Por favor, envie o arquivo XML correto"}, status=status.HTTP_400_BAD_REQUEST)
        ServicoCronograma.objects.filter(cronograma=cronograma).delete()

        
        import xml.etree.ElementTree as ET
        tree = ET.parse(file)
        root = tree.getroot()

        ns = {'p': 'http://schemas.microsoft.com/project'}

        u_lvl1 = ''
        u_lvl2 = ''
        u_lvl3 = ''

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

            inicio_str = inicio.text if inicio is not None else None
            fim_str = fim.text if fim is not None else None

            data_inicio = datetime.strptime(inicio_str.split(
                'T')[0], '%Y-%m-%d').date() if inicio_str else None
            data_fim = datetime.strptime(fim_str.split(
                'T')[0], '%Y-%m-%d').date() if fim_str else None

            dias = (data_fim - data_inicio).days if data_inicio and data_fim else 0

            data = {
                'cronograma': cronograma,
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
                    u_lvl1 = ServicoCronograma.objects.all().last()
                elif intnivel == 2:
                    u_lvl2 = ServicoCronograma.objects.all().last()
                elif intnivel == 3:
                    u_lvl3 = ServicoCronograma.objects.all().last()

            else:
                print(serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Cronograma importado com sucesso"}, status=status.HTTP_200_OK)
