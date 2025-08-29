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
        for r in col['pontos']:
            h, m = map(int, r['horas_trabalhadas'].split(":"))
            horas_trab = timedelta(hours=h, minutes=m)
            data_print = formatar_data_com_dia(r['data'])
            dia_semana = formatar_data_com_dia(r['data'])[-3:]
            horas_extras = timedelta()

            if dia_semana == "DOM" or r['feriado'] == 'True':
                hr_fer += horas_trab
                horas_extras = horas_trab
            elif dia_semana not in ["SEX", "SÁB", "DOM"]:
                if horas_trab < timedelta(hours=9):
                    hr_falt += timedelta(hours=9) - horas_trab
                    horas_extras = f'-{str(timedelta(hours=9) - horas_trab)}'
                elif horas_trab > timedelta(hours=9):
                    hr_ext += horas_trab - timedelta(hours=9)
                    horas_extras = horas_trab - timedelta(hours=9)
            elif dia_semana == "SEX":
                if horas_trab < timedelta(hours=8):
                    hr_falt += timedelta(hours=8) - horas_trab
                    horas_extras = f'-{str(timedelta(hours=8) - horas_trab)}'
                elif horas_trab > timedelta(hours=8):
                    hr_ext += horas_trab - timedelta(hours=8)
                    horas_extras = horas_trab - timedelta(hours=8)
            elif dia_semana == "SÁB":
                hr_ext += horas_trab
                horas_extras = horas_trab

            pontos += f"""
                    <tr class={'sabado' if dia_semana == 'SÁB' else 'domingo' if dia_semana == 'DOM' else 'feriado' if r['feriado'] == 'True' else ''}>
                        <td>{data_print}</td>
                        <td>{r['entrada_manha']}</td>
                        <td>{r['saida_manha']}</td>
                        <td>{r['entrada_tarde']}</td>
                        <td>{r['saida_tarde']}</td>
                        <td>{horas_trab}</td>
                        <td class={'positivo' if not str(horas_extras).startswith('-') else 'negativo'}>{horas_extras}</td>
                    </tr>
    """

        html_content += f"""<body>
        <h2>FREQUÊNCIA DIÁRIA</h2>
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
