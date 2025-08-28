from django.db.models import Max
from datetime import timedelta
from engenharia.models import Cronograma, ServicoCronograma

def ajustar_cronograma_em_lote(cronograma):
    servicos = ServicoCronograma.objects.filter(cronograma=cronograma).select_related('pai').prefetch_related('predecessores', 'sucessores')
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
    return