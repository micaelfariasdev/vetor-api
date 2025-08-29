from weasyprint import HTML
from datetime import datetime, time, timedelta
import locale
import calendar


locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")


data = [
    {
        "colaborador": "micael farias",
        "cargo": "Auxiliar de Engenharia",
        "obra": "sky 2",
        "pontos": [
            {
                "data": "2025-08-05",
                "feriado": 'False',
                "entrada_manha": "12:03:00",
                "saida_manha": "12:04:00",
                "entrada_tarde": "12:24:00",
                "saida_tarde": "12:45:00",
                "horas_trabalhadas": "00:22"
            },
            {
                "data": "2025-08-06",
                "feriado": 'False',
                "entrada_manha": "12:03:00",
                "saida_manha": "12:04:00",
                "entrada_tarde": "12:24:00",
                "saida_tarde": "12:45:00",
                "horas_trabalhadas": "00:22"
            },
            {
                "data": "2025-08-07",
                "feriado": 'False',
                "entrada_manha": "12:03:00",
                "saida_manha": "12:04:00",
                "entrada_tarde": "12:24:00",
                "saida_tarde": "12:45:00",
                "horas_trabalhadas": "00:22"
            },
            {
                "data": "2025-08-08",
                "feriado": 'True',
                "entrada_manha": "12:03:00",
                "saida_manha": "12:04:00",
                "entrada_tarde": "12:24:00",
                "saida_tarde": "12:45:00",
                "horas_trabalhadas": "00:22"
            },
            {
                "data": "2025-08-09",
                "feriado": 'False',
                "entrada_manha": "12:03:00",
                "saida_manha": "12:04:00",
                "entrada_tarde": "12:24:00",
                "saida_tarde": "12:45:00",
                "horas_trabalhadas": "00:22"
            },
            {
                "data": "2025-08-10",
                "feriado": 'False',
                "entrada_manha": "12:03:00",
                "saida_manha": "12:04:00",
                "entrada_tarde": "12:24:00",
                "saida_tarde": "12:45:00",
                "horas_trabalhadas": "00:22"
            },
            {
                "data": "2025-08-27",
                "feriado": 'False',
                "entrada_manha": "07:00:00",
                "saida_manha": "13:00:00",
                "entrada_tarde": "12:00:00",
                "saida_tarde": "17:00:00",
                "horas_trabalhadas": "11:00"
            }
        ]
    }
]


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

        h2 {
            text-align: center;
        }

        th,
        td {
            border: 1px solid #000;
            padding: 5px;
            text-align: center;
        }

        th {
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
            width: 100%;
            display: flex;
            flex-direction: column;
            padding: 10px;
        }

        .cabeçalho span strong {
            padding-right: 5px;
        }

        .tabela {
            width: 250px;
            display: grid;
            grid-template-columns: 5fr 2fr;
        }

        .tabela div,
        .cabeçalho div {
            margin: -1px;
            padding: 5px;
            border: 2px solid black;
            font-weight: bold;
        }

        .topo {
            width: 105%;
            display: flex;
            align-items: center;
        }
        .page-break {
            page-break-after: always;
        }
    </style>
</head>
"""


def formatar_data_com_dia(data_str):
    # data_str = "2025-08-27" (formato YYYY-MM-DD)
    data = datetime.strptime(data_str, "%Y-%m-%d")
    dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    dia_sigla = dias_semana[data.weekday()]  # weekday() 0 = segunda
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
            horas_extras= horas_trab
        elif dia_semana not in ["SEX", "SÁB", "DOM"]:
            if horas_trab < timedelta(hours=9):
                hr_falt += timedelta(hours=9) - horas_trab
                horas_extras = f'-{str(timedelta(hours=9) - horas_trab)}' 
            elif horas_trab > timedelta(hours=9):
                hr_ext += horas_trab - timedelta(hours=9)
                horas_extras= horas_trab - timedelta(hours=9)
        elif dia_semana == "SEX":
            if horas_trab < timedelta(hours=8):
                hr_falt += timedelta(hours=8) - horas_trab
                horas_extras = f'-{str(timedelta(hours=8) - horas_trab)}'
            elif horas_trab > timedelta(hours=8):
                hr_ext += horas_trab - timedelta(hours=8)
                horas_extras = horas_trab - timedelta(hours=8)
        elif dia_semana == "SÁB":
            hr_ext += horas_trab
            horas_extras= horas_trab

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
    <div class="topo">
        <div class='cabeçalho'>
            <div><strong>OBRA:</strong>{col['obra']}</div>
            <div><strong>FUNCIONARIO:</strong>{col['colaborador']}</div>
            <div><strong>CARGO:</strong>{col['cargo']}</div>
        </div>
        <div class="tabela">
            <div>HORAS FALTANTES</div>
            <div>{formatar_horas(hr_falt)}</div>
            <div>HORAS EXTRAS</div>
            <div>{formatar_horas(hr_ext)}</div>
            <div>HORAS FERIADOS/DOMINGOS</div>
            <div>{formatar_horas(hr_fer)}</div>
        </div>
    </div>
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
HTML(string=html_content).write_pdf("frequencia_diaria.pdf")
print("PDF gerado com sucesso!")
