from django.db.models import Max
from datetime import timedelta
from engenharia.models import Cronograma, ServicoCronograma


def ajustar_cronograma_em_lote(cronograma):
    servicos = ServicoCronograma.objects.filter(cronograma=cronograma).select_related(
        'pai').prefetch_related('predecessores', 'sucessores')
    servicos = list(servicos.order_by('nivel', 'id'))

    servicos_map = {s.pk: s for s in servicos}
    atualizados = []

    for servico in servicos:
        duracao = servico.dias or 0
        maiores_fins = [p.fim for p in servico.predecessores.all() if p.fim]
        if maiores_fins:
            maior_fim = max(maiores_fins)
            nova_inicio = maior_fim + timedelta(days=1)
            nova_fim = nova_inicio + timedelta(days=duracao)
        else:
            nova_inicio = servico.inicio
            nova_fim = servico.inicio + timedelta(days=duracao)

        if servico.inicio != nova_inicio or servico.fim != nova_fim:
            servico.inicio = nova_inicio
            servico.fim = nova_fim
            atualizados.append(servico)

    if atualizados:
        ServicoCronograma.objects.bulk_update(atualizados, ['inicio', 'fim'])

    maior_fim = max((s.fim for s in servicos if s.fim), default=None)
    if cronograma.final != maior_fim:
        cronograma.final = maior_fim
        cronograma.save(update_fields=['final'])


def gerar_pdf_ponto(registros):
    from weasyprint import HTML
    from datetime import datetime, time, timedelta
    import locale
    import calendar

    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

    data = registros
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    from datetime import date, timedelta

    def gerar_lista_datas(mes, ano):
        if mes == 1:
            mes_anterior = 12
            ano_anterior = ano - 1
        else:
            mes_anterior = mes - 1
            ano_anterior = ano

        data_inicio = date(ano_anterior, mes_anterior, 26)
        data_fim = date(ano, mes, 25)

        lista_de_datas = []
        data_atual = data_inicio

        while data_atual <= data_fim:
            lista_de_datas.append(data_atual)
            data_atual += timedelta(days=1)

        return lista_de_datas


# Exemplo de uso

    html_content = """
    <html>

    <head>
        <style>
        body {
            font-family: Arial, sans-serif;
            font-size: 10px;
            width: 80%;
            display: flex
            justify-items: center;
            align-items: center;

        }

        table {
            border-collapse: collapse;
            width: 120%;
        }

        .tabela-pontos h2 {
            text-align: center;
        }

        .tabela-pontos th,
        .tabela-pontos td {
            border: 1px solid #000;
            padding: 5px;
            text-align: center;
        }

        .tabela-pontos th {
            background-color: #d3d3d3;
        }

        .legenda {
            margin-bottom: 10px;
        }

        .block-legenda{
            display: inline-block;
            width: 10px;
            height: 10px;
            border: 1px solid black;
            margin-left: 2px;
            vertical-align: middle;
        }

        .sabado {
            background-color: #c8e6c9;
        }

        .domingo {
            background-color: #E6868A;
        }

        .feriado {
            background-color: #FABD7E;
        }

        .negativo {
            color: red;
        }

        .positivo {
            color: green;
        }

        .header-table td {
            font-weight: bold;
        }

        

        .observacoes {
            opacity: 0.7;
            transform: scale(.9);
            font-style: italic;
            border: 1px solid black;
            border-radius: 5px;
            padding: 5px;
            margin-bottom: 5px;
            font-size: 12px;
            text-align: justify;
            width: 120%;
        }

        .cabeçalho {
            border-collapse: collapse;
            width: 120%;
            text-align: left;
        }

        .cabeçalho th,
        .cabeçalho td {
            border: 1px solid #000;
            padding: 8px;
        }

        
        .cabeçalho .col1 {
            width: 60%;
        }
        .cabeçalho .col2 {
            width: 30%;
        }
        .cabeçalho .col3 {
            width: 10%;
        }
        .page-break {
            page-break-after: always;
        }
    </style>
    </head>
    """

    def formatar_data_com_dia(data_str):
        data = data_str
        dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
        dia_sigla = dias_semana[data.weekday()]
        data_formatada = data.strftime("%d/%m/%Y")
        return f'{data_formatada} • {dia_sigla}'

    def formatar_horas(time):
        total_segundos = time.total_seconds()
        horas = int(total_segundos // 3600)
        minutos = int((total_segundos % 3600) // 60)
        segundos = int(total_segundos % 60)

        resultado = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        return resultado

    for col in data:
        pontos = ""
        hr_falt = timedelta()
        hr_ext = timedelta()
        hr_fer = timedelta()

        for i, d in enumerate(gerar_lista_datas(col['mes'], int(col['ano']))):
            registro_encontrado = None

            try:
                registro_encontrado = list(
                    filter(lambda r: r['data'] == d, col['pontos']))[0]

            except IndexError:
                pass

            if registro_encontrado:
                h, m = registro_encontrado['horas_trabalhadas'].split(":")
                horas_trab = timedelta(hours=int(h), minutes=int(m))
                dia_semana = formatar_data_com_dia(d)[-3:]
                horas_extras = timedelta()

                if dia_semana == "DOM" or registro_encontrado['feriado'] == 'True':
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
                dia_semana = formatar_data_com_dia(d)[-3:]
                is_weekend = 'sabado' if dia_semana == 'SÁB' else 'domingo' if dia_semana == 'DOM' else ''

                pontos += f"""
                        <tr class="{is_weekend}">
                            <td>{formatar_data_com_dia(d)}</td>
                            <td>{registro_encontrado['entrada_manha']}</td>
                            <td>{registro_encontrado['saida_manha']}</td>
                            <td>{registro_encontrado['entrada_tarde']}</td>
                            <td>{registro_encontrado['saida_tarde']}</td>
                            <td>{registro_encontrado['horas_trabalhadas']}</td>
                            <td class={'positivo' if not str(horas_extras).startswith('-') else 'negativo'}>{horas_extras}</td>
                        </tr>
                """
            else:
                dia_semana = formatar_data_com_dia(d)[-3:]
                is_weekend = 'sabado' if dia_semana == 'SÁB' else 'domingo' if dia_semana == 'DOM' else ''

                pontos += f"""
                        <tr class="{is_weekend}">
                            <td>{formatar_data_com_dia(d)}</td>
                            <td>-</td>
                            <td>-</td>
                            <td>-</td>
                            <td>-</td>
                            <td>00:00</td>
                            <td>-</td>
                        </tr>
                """
        html_content += f"""<body>
        <h2>FREQUÊNCIA DIÁRIA DO MÊS DE {meses[col['mes']-1].upper()}</h2>
        <table class="cabeçalho" >
            <tr>
                <td class="col1"><strong>OBRA:</strong> {col['obra']}</td>
                <td class="col2"><strong>HORAS FALTANTES</strong></td>
                <td class="col3">{formatar_horas(hr_falt)}</td>
            </tr>
            <tr>
                <td class="col1"><strong>FUNCIONÁRIO:</strong> {col['colaborador']}</td>
                <td><strong>HORAS EXTRAS</strong></td>
                <td>{formatar_horas(hr_ext)}</td>
            </tr>
            <tr>
                <td class="col1"><strong>CARGO:</strong> {col['cargo']}</td>
                <td><strong>HORAS FERIADOS/DOMINGOS</strong></td>
                <td>{formatar_horas(hr_fer)}</td>
            </tr>
        </table>  
        <div class="observacoes">
            <p>A jornada de trabalho de segunda a quinta é de 9 horas diárias, das 07:00 às 17:00, com 1 hora de intervalo
                para almoço das 12:00 às 13:00. Às sextas-feiras, a jornada é de 8 horas, das 07:00 às 16:00, com o mesmo
                intervalo de almoço.</p>
        </div>
        <div class="legenda">
            <span>Sábado = <span class="block-legenda sabado"></span></span>
            <span>Domingo = <span class="block-legenda domingo"></span></span>
            <span>Feriado = <span class="block-legenda feriado"></span></span>
        </div>

        <table class="tabela-pontos">
            <thead>
                <tr>
                    <th>DATA</th>
                    <th>ENTRADA</th>
                    <th>SAÍDA</th>
                    <th>ENTRADA</th>
                    <th>SAÍDA</th>
                    <th>QTDE. HORAS</th>
                    <th>SALDO</th>
                </tr>
            </thead>
            <tbody>
    """
        html_content += pontos
        html_content += f"""    
            </tbody>
        </table>
        <div class="page-break">
        </div>
        
    </body>

    </html>
    """

    # Gerando PDF
    pdf = HTML(string=html_content).write_pdf()
    return pdf
