from datetime import timedelta, date

data = {
    "colaborador_id": 2,
    "mes": 9,
    "ano": 2025,
    "registros": [
        {
            "data": "01",
            "valores": [
                "23:04",
                "",
                "",
                ""
            ]
        }
    ]
}

pontos = data['registros']
for ponto in pontos:
    dia = date(int(data['ano']), int(data['mes']), int(ponto['data']))
    
