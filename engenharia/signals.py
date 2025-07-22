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
def atualizar_dados_cronograma(sender, instance, **kwargs):
    instance.ajustar_datas_por_dependencia()

    cronograma = instance.cronograma
    if cronograma.final is None or instance.fim > cronograma.final:
        cronograma.final = instance.fim
        cronograma.save(update_fields=['final'])
