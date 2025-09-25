from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from django_filters.rest_framework import DjangoFilterBackend

from engenharia.models import Ponto, MesPonto, Colaborador
from ..serializer import PontoSerializer, MesPontoSerializer, ColaboradorSerializer

from datetime import date, time, datetime, timedelta
from itertools import groupby
from operator import itemgetter
import locale
import calendar
import io
import requests


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


def gerar_datas_no_intervalo(data_inicio, data_fim):
    """
    Gera uma lista de objetos date entre duas datas.

    Args:
        data_inicio (datetime.date): A data de início (inclusive).
        data_fim (datetime.date): A data final (inclusive).

    Returns:
        list: Uma lista de objetos date.
    """
    lista_de_datas = []
    data_atual = data_inicio

    # Adiciona 1 dia por vez até chegar na data final
    while data_atual <= data_fim:
        lista_de_datas.append(data_atual)
        data_atual += timedelta(days=1)

    return lista_de_datas


def formatar_semana(data_str):
    data = data_str
    dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    dia_sigla = dias_semana[data.weekday()]
    data_formatada = data.strftime("%d/%m/%Y")

    return dia_sigla


def formatar_horas(time):
    total_segundos = time.total_seconds()
    horas = int(total_segundos // 3600)
    minutos = int((total_segundos % 3600) // 60)
    # segundos = int(total_segundos % 60)

    resultado = f"{horas:02d}:{minutos:02d}"
    return resultado


@api_view(['GET'])
def pdf_pontos_relatorio(request, mes_id, col=None):
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

        resultado = []
        if col:
            colaborador = mes_ponto.obra.colaboradores.get(id=col)
            pontos_dic = {}
            mes_completo = gerar_datas_no_intervalo(ini, fim)
            for dia in mes_completo:
                dia_semana = formatar_semana(dia)
                dia = dia.isoformat()
                pontos_dic[dia] = [dia_semana]
            pontos = colaborador.pontos.filter(data__range=[ini, fim])
            if not pontos.exists():
                return HttpResponse("ponto não encontrado.", status=200)
            hr_falt = timedelta()
            hr_ext = timedelta()
            hr_fer = timedelta()
            falta = 0
            pontos = list(pontos.values())
            registros_feriado = filter(
                lambda registro: registro['feriado'] == True, pontos)
            datas_feriado = [registro['data']
                             for registro in registros_feriado]
            for feriado in datas_feriado:
                if formatar_semana(feriado) == "SÁB":
                    data_inicio = feriado - timedelta(days=5)
                    data_fim = feriado - timedelta(days=1)
                    semana = list(
                        filter(lambda r:
                               data_inicio <= r['data'] <= data_fim, pontos))
                    for s in semana:
                        s['sem_feriado'] = True

            for ponto in pontos:
                dia_semana = formatar_semana(ponto['data'])
                dataPonto = []
                dataPonto.append(dia_semana)
                dataPonto.append(str(ponto['entrada_manha'])[:5])
                dataPonto.append(str(ponto['saida_manha'])[:5])
                dataPonto.append(str(ponto['entrada_tarde'])[:5])
                dataPonto.append(str(ponto['saida_tarde'])[:5])
                dataPonto.append(ponto['horas_trabalhadas'])

                if ponto['atestado'] == True or ponto['ferias'] == True:
                    dataPonto.append('00:00')
                    if ponto['atestado']:
                        dataPonto.append('atestado')
                    if ponto['ferias']:
                        dataPonto.append('ferias')
                    data_str = ponto['data'].isoformat()
                    pontos_dic[data_str] = dataPonto
                    continue
                elif ponto['falta'] == True and ponto['data'].month == mes_ponto.mes:
                    falta += 1
                    dataPonto.append('00:00')
                    if ponto['falta']:
                        dataPonto.append('falta')
                    data_str = ponto['data'].isoformat()
                    pontos_dic[data_str] = dataPonto
                    continue
                elif ponto['falta'] == True:
                    dataPonto.append('00:00')
                    if ponto['falta']:
                        dataPonto.append('falta')
                    data_str = ponto['data'].isoformat()
                    pontos_dic[data_str] = dataPonto
                    continue
                else:
                    h, m = ponto['horas_trabalhadas'].split(':')
                    horas_trab = timedelta(hours=int(h), minutes=int(m))
                    dif_hora = timedelta(hours=int(h), minutes=int(m))

                    if 'sem_feriado' in ponto:
                        jornada_diaria = timedelta(hours=8)
                        if horas_trab < jornada_diaria:
                            hr_falt += jornada_diaria - horas_trab
                            dif_hora = horas_trab - jornada_diaria
                        elif horas_trab >= jornada_diaria:
                            hr_ext += horas_trab - jornada_diaria
                            dif_hora = horas_trab - jornada_diaria
                    elif dia_semana == "DOM" or ponto['feriado'] == True:
                        hr_fer += horas_trab
                        dif_hora = horas_trab
                    elif dia_semana not in ["SEX", "SÁB", "DOM"]:
                        jornada_diaria = timedelta(hours=9)
                        if horas_trab <= jornada_diaria:
                            hr_falt += jornada_diaria - horas_trab
                            dif_hora = horas_trab - jornada_diaria
                        elif horas_trab > jornada_diaria:
                            hr_ext += horas_trab - jornada_diaria
                            dif_hora = horas_trab - jornada_diaria
                    elif dia_semana == "SEX":
                        jornada_diaria = timedelta(hours=8)
                        if horas_trab <= jornada_diaria:
                            hr_falt += jornada_diaria - horas_trab
                            dif_hora = horas_trab - jornada_diaria
                        elif horas_trab > jornada_diaria:
                            hr_ext += horas_trab - jornada_diaria
                            dif_hora = horas_trab - jornada_diaria
                    elif dia_semana == "SÁB":
                        hr_ext += horas_trab
                        dif_hora = horas_trab

            
                dataPonto.append(formatar_horas(dif_hora))
                if ponto['feriado']:
                    dataPonto.append('feriado')
                elif 'sem_feriado' in ponto:
                    dataPonto.append('sem_feriado')
                

                data_str = ponto['data'].isoformat()
                pontos_dic[data_str] = dataPonto

            dados = ColaboradorSerializer(colaborador).data
            if not dados:
                return HttpResponse("dados não encontrado.", status=200)
            dados['horas-faltando'] = formatar_horas(hr_falt)
            dados['horas-extras'] = formatar_horas(hr_ext)
            dados['horas-feriado-domingo'] = formatar_horas(hr_fer)
            dados['falta'] = falta
            dados['mes'] = mes_ponto.mes
            dados['ano'] = mes_ponto.ano
            data = {
                'dados': dados,
                'pontos': pontos_dic
            }
            resultado.append(data)

        else:
            colaboradores = mes_ponto.obra.colaboradores.all()

            for colaborador in colaboradores:
                pontos_dic = {}
                mes_completo = gerar_datas_no_intervalo(ini, fim)
                for dia in mes_completo:
                    dia_semana = formatar_semana(dia)
                    dia = dia.isoformat()
                    pontos_dic[dia] = [dia_semana]
                pontos = colaborador.pontos.filter(data__range=[ini, fim])
                hr_falt = timedelta()
                hr_ext = timedelta()
                hr_fer = timedelta()
                falta = 0
                pontos = list(pontos.values())
                registros_feriado = filter(
                    lambda registro: registro['feriado'] == True, pontos)
                datas_feriado = [registro['data']
                                 for registro in registros_feriado]
                for feriado in datas_feriado:
                    if formatar_semana(feriado) == "SÁB":
                        data_inicio = feriado - timedelta(days=5)
                        data_fim = feriado - timedelta(days=1)
                        semana = list(
                            filter(lambda r:
                                   data_inicio <= r['data'] <= data_fim, pontos))
                        for s in semana:
                            s['sem_feriado'] = True

                for ponto in pontos:
                    dia_semana = formatar_semana(ponto['data'])
                    dataPonto = []
                    dataPonto.append(dia_semana)
                    dataPonto.append(str(ponto['entrada_manha'])[:5])
                    dataPonto.append(str(ponto['saida_manha'])[:5])
                    dataPonto.append(str(ponto['entrada_tarde'])[:5])
                    dataPonto.append(str(ponto['saida_tarde'])[:5])
                    dataPonto.append(ponto['horas_trabalhadas'])

                    if ponto['atestado'] == True or ponto['ferias'] == True:
                        dataPonto.append('00:00')
                        if ponto['atestado']:
                            dataPonto.append('atestado')
                        if ponto['ferias']:
                            dataPonto.append('ferias')
                        data_str = ponto['data'].isoformat()
                        pontos_dic[data_str] = dataPonto
                        continue
                    elif ponto['falta'] == True and ponto['data'].month == mes_ponto.mes:
                        falta += 1
                        dataPonto.append('00:00')
                        if ponto['falta']:
                            dataPonto.append('falta')
                        data_str = ponto['data'].isoformat()
                        pontos_dic[data_str] = dataPonto
                        continue
                    elif ponto['falta'] == True:
                        dataPonto.append('00:00')
                        if ponto['falta']:
                            dataPonto.append('falta')
                        data_str = ponto['data'].isoformat()
                        pontos_dic[data_str] = dataPonto
                        continue
                    else:
                        h, m = ponto['horas_trabalhadas'].split(':')
                        horas_trab = timedelta(hours=int(h), minutes=int(m))
                        dif_hora = timedelta(hours=int(h), minutes=int(m))

                        if 'sem_feriado' in ponto:
                            jornada_diaria = timedelta(hours=8)
                            if horas_trab < jornada_diaria:
                                hr_falt += jornada_diaria - horas_trab
                                dif_hora = horas_trab - jornada_diaria
                            elif horas_trab >= jornada_diaria:
                                hr_ext += horas_trab - jornada_diaria
                                dif_hora = horas_trab - jornada_diaria
                        elif dia_semana == "DOM" or ponto['feriado'] == True:
                            hr_fer += horas_trab
                            dif_hora = horas_trab
                        elif dia_semana not in ["SEX", "SÁB", "DOM"]:
                            jornada_diaria = timedelta(hours=9)
                            if horas_trab <= jornada_diaria:
                                hr_falt += jornada_diaria - horas_trab
                                dif_hora = horas_trab - jornada_diaria
                            elif horas_trab > jornada_diaria:
                                hr_ext += horas_trab - jornada_diaria
                                dif_hora = horas_trab - jornada_diaria
                        elif dia_semana == "SEX":
                            jornada_diaria = timedelta(hours=8)
                            if horas_trab <= jornada_diaria:
                                hr_falt += jornada_diaria - horas_trab
                                dif_hora = horas_trab - jornada_diaria
                            elif horas_trab > jornada_diaria:
                                hr_ext += horas_trab - jornada_diaria
                                dif_hora = horas_trab - jornada_diaria
                        elif dia_semana == "SÁB":
                            hr_ext += horas_trab
                            dif_hora = horas_trab

                
                    dataPonto.append(formatar_horas(dif_hora))
                    if ponto['feriado']:
                        dataPonto.append('feriado')
                    elif 'sem_feriado' in ponto:
                        dataPonto.append('sem_feriado')
                    

                    data_str = ponto['data'].isoformat()
                    pontos_dic[data_str] = dataPonto
                
                data = {
                    'dados': dados,
                    'pontos': pontos_dic
                }
                resultado.append(data)

        import json
        with open("dados.json", "w", encoding="utf-8") as arquivo:
            json.dump(resultado, arquivo, ensure_ascii=False, indent=4)

        pdf = requests.post(
        'http://64.181.171.161/relatorio/ponto', json=resultado)

        return HttpResponse(pdf)
        

    except MesPonto.DoesNotExist:
        return HttpResponse("Mês de ponto não encontrado.", status=404)
    except Exception as e:
        return HttpResponse(f"Erro ao gerar o PDF: {str(e)}", status=500)


@api_view(['GET'])
def proxy_download_zip(request, ano, mes):
    url_externa = f'https://64.181.171.161/pontos/{ano}/{mes}/zip'

    resposta = requests.get(url_externa, stream=True)
    resposta.raise_for_status()

    # Define os cabeçalhos para o download do arquivo
    nome_do_arquivo = f'pontos_{ano}_{mes}.zip'
    response = HttpResponse(
        resposta.content, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{nome_do_arquivo}"'

    return response
