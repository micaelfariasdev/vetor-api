from weasyprint import HTML
from datetime import timedelta
from engenharia.models import ServicoCronograma


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

    def formatar_data_com_dia(data_obj):
        dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
        dia_sigla = dias_semana[data_obj.weekday()]
        data_formatada = data_obj.strftime("%d/%m/%Y")
        return f"{data_formatada} • {dia_sigla}"

    def formatar_horas(td: timedelta):
        total_segundos = int(td.total_seconds())
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        return f"{horas:02d}:{minutos:02d}"

    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; font-size: 10px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #000; padding: 5px; text-align: center; }
            th { background-color: #d3d3d3; }
            .positivo { color: green; }
            .negativo { color: red; }
            .sabado { background-color: #c8e6c9; }
            .domingo { background-color: #E6868A; }
            .feriado { background-color: #FABD7E; }
            .page-break { page-break-after: always; }
            .cabeçalho span { display:block; margin-bottom:3px; }
        </style>
    </head>
    <body>
    """

    for col in registros:
        hr_falt = timedelta()
        hr_ext = timedelta()
        hr_fer = timedelta()
        pontos_html = ""

        for r in col['pontos']:
            h, m = map(int, r['horas_trabalhadas'].split(":"))
            horas_trab = timedelta(hours=h, minutes=m)
            data_print = formatar_data_com_dia(r['data'])
            dia_semana = data_print[-3:]
            feriado = r.get('feriado', False)
            saldo = timedelta()

            if dia_semana == "DOM" or feriado:
                hr_fer += horas_trab
                saldo = horas_trab
            elif dia_semana not in ["SEX", "SÁB", "DOM"]:
                if horas_trab < timedelta(hours=9):
                    hr_falt += timedelta(hours=9) - horas_trab
                    saldo = -(timedelta(hours=9) - horas_trab)
                else:
                    hr_ext += horas_trab - timedelta(hours=9)
                    saldo = horas_trab - timedelta(hours=9)
            elif dia_semana == "SEX":
                if horas_trab < timedelta(hours=8):
                    hr_falt += timedelta(hours=8) - horas_trab
                    saldo = -(timedelta(hours=8) - horas_trab)
                else:
                    hr_ext += horas_trab - timedelta(hours=8)
                    saldo = horas_trab - timedelta(hours=8)
            elif dia_semana == "SÁB":
                hr_ext += horas_trab
                saldo = horas_trab

            cls = 'sabado' if dia_semana == "SÁB" else 'domingo' if dia_semana == "DOM" else 'feriado' if feriado else ''
            cls_saldo = 'positivo' if saldo >= timedelta(0) else 'negativo'
            saldo_str = formatar_horas(abs(saldo)) if isinstance(
                saldo, timedelta) else saldo

            pontos_html += f"""
                <tr class="{cls}">
                    <td>{data_print}</td>
                    <td>{r['entrada_manha']}</td>
                    <td>{r['saida_manha']}</td>
                    <td>{r['entrada_tarde']}</td>
                    <td>{r['saida_tarde']}</td>
                    <td>{formatar_horas(horas_trab)}</td>
                    <td class="{cls_saldo}">{saldo_str}</td>
                </tr>
            """

        html_content += f"""
        <h2>FREQUÊNCIA DIÁRIA</h2>
        <div class="cabeçalho">
            <span><strong>OBRA:</strong> {col['obra']}</span>
            <span><strong>FUNCIONÁRIO:</strong> {col['colaborador']}</span>
            <span><strong>CARGO:</strong> {col['cargo']}</span>
        </div>
        <div>
            <table>
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
                    {pontos_html}
                </tbody>
            </table>
        </div>
        <div class="page-break"></div>
        """

    html_content += "</body></html>"

    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
