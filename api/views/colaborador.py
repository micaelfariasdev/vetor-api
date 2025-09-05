from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from ..serializer import ColaboradorSerializer
from engenharia.models import Colaborador
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, time, timedelta, date
import locale
import calendar
import io

locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")


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
    segundos = int(total_segundos % 60)

    resultado = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    return resultado


class ColaboradorApiViewSet(ModelViewSet):
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'

    @action(detail=True, methods=["get"], url_path="pontos")
    def colaborador_pontos(self, request, pk=None):
        colaborador = self.get_object()
        pontos = colaborador.pontos.all()
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
            if ponto['atestado'] == True:
                ...
            elif ponto['falta'] == True:
                falta += 1
            else:
                dia_semana = formatar_semana(ponto['data'])
                h, m = ponto['horas_trabalhadas'].split(':')
                horas_trab = timedelta(hours=int(h), minutes=int(m))

                if 'sem_feriado' in ponto:
                    jornada_diaria = timedelta(hours=8)
                    if horas_trab < jornada_diaria:
                        hr_falt += jornada_diaria - horas_trab
                        horas_extras = f'-{str(jornada_diaria - horas_trab)}'
                    elif horas_trab > jornada_diaria:
                        hr_ext += horas_trab - jornada_diaria
                        horas_extras = horas_trab - jornada_diaria
                elif dia_semana == "DOM" or ponto['feriado'] == 'True':
                    hr_fer += horas_trab
                    horas_extras = horas_trab
                elif dia_semana not in ["SEX", "SÁB", "DOM"]:
                    jornada_diaria = timedelta(hours=9)
                    if horas_trab < jornada_diaria:
                        hr_falt += jornada_diaria - horas_trab
                        horas_extras = f'-{str(jornada_diaria - horas_trab)}'
                    elif horas_trab > jornada_diaria:
                        hr_ext += horas_trab - jornada_diaria
                        horas_extras = horas_trab - jornada_diaria
                elif dia_semana == "SEX":
                    jornada_diaria = timedelta(hours=8)
                    if horas_trab < jornada_diaria:
                        hr_falt += jornada_diaria - horas_trab
                        horas_extras = f'-{str(jornada_diaria - horas_trab)}'
                    elif horas_trab > jornada_diaria:
                        hr_ext += horas_trab - jornada_diaria
                        horas_extras = horas_trab - jornada_diaria
                elif dia_semana == "SÁB":
                    hr_ext += horas_trab
                    horas_extras = horas_trab

        dados = self.serializer_class(colaborador).data
        dados['horas-faltando'] = formatar_horas(hr_falt)
        dados['horas-extras'] = formatar_horas(hr_ext)
        dados['horas-feriado-domingo'] = formatar_horas(hr_fer)
        dados['falta'] = falta

        data = {
            'dados': dados,
            'pontos': pontos
        }
        return Response(data)
