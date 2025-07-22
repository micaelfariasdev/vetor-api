from .models import ServicoCronograma, Cronograma
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.db.models import Max


@receiver(m2m_changed, sender=ServicoCronograma.predecessores.through)
def atualizar_sucessores_quando_dependencia_mudar(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.ajustar_datas_por_dependencia()
        instance.save(update_fields=['inicio', 'fim'])


@receiver(post_save, sender=ServicoCronograma)
def atualizar_sucessores_ao_salvar(sender, instance, **kwargs):
    instance.ajustar_datas_por_dependencia()


@receiver(post_save, sender=ServicoCronograma)
def atualizar_fim_cronograma(sender, instance, **kwargs):
    cronograma = instance.cronograma  # Corrigido: campo minúsculo
    maior_fim = cronograma.servicos.aggregate(Max('fim'))['fim__max']
    if maior_fim and cronograma.final != maior_fim:
        cronograma.final = maior_fim
        cronograma.save(update_fields=['final'])
