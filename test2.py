from weasyprint import HTML

html_content = """
<html>
<head>
<style>
body { font-family: Arial, sans-serif; font-size: 12px; }
h1 { text-align: center; }
table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #000; padding: 4px; text-align: left; }
.page-break { page-break-after: always; }
</style>
</head>
<body>

<h1>Relatório de Registros</h1>

<table>
<tr><th>Data</th><th>Dia</th><th>Entrada</th><th>Saída</th><th>Horas</th></tr>
"""

# Gerando várias linhas para simular múltiplas páginas
for i in range(1, 51):
    html_content += f"<tr><td>01/{i:02d}/2025</td><td>SEG</td><td>07:00</td><td>17:00</td><td>09:00</td></tr>"
    if i % 20 == 0:  # quebra de página a cada 20 linhas
        html_content += '<div class="page-break"></div>'

html_content += """
</table>
</body>
</html>
"""

HTML(string=html_content).write_pdf("relatorio.pdf")
