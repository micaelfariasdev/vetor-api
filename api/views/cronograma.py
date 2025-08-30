from ..utils import ajustar_cronograma_em_lote
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from ..serializer import CronogramaSerializer, ServicoCronogramaSerializer
from engenharia.models import Cronograma, ServicoCronograma
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from datetime import datetime


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
