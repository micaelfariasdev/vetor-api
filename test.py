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


print(gerar_lista_datas(8, 2025))
