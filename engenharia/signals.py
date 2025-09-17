from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Obras, ServicoUnidade, Servicos, Unidade

# O decorator @receiver conecta a função 'create_servico_unidade' ao signal m2m_changed.
@receiver(m2m_changed, sender=Obras.servicos.through)
def create_servico_unidade(sender, instance, action, **kwargs):
    """
    Cria entradas de ServicoUnidade para todas as unidades da obra
    quando um serviço é adicionado a uma obra.
    """
    
    # Queremos agir apenas quando um item é ADICIONADO (post_add)
    # ou quando vários itens são adicionados de uma vez (pre_add, post_add)
    if action == 'post_add':
        # 'instance' aqui é o objeto Obras (a obra que foi modificada)
        obra = instance 
        
        # 'pk_set' contém os IDs (PKs) dos Servicos que foram adicionados/removidos
        servico_ids = kwargs.get('pk_set')
        
        if servico_ids:
            # 1. Encontrar as unidades que pertencem a esta obra
            unidades = Unidade.objects.filter(obra=obra)
            
            # 2. Encontrar os serviços que foram adicionados
            servicos = Servicos.objects.filter(id__in=servico_ids)
            
            # Lista para armazenar novos objetos ServicoUnidade
            servicos_unidade_a_criar = []
            
            for unidade in unidades:
                for servico in servicos:
                    # Verifica se o ServicoUnidade já existe para evitar duplicatas (melhor do que tentar criar e falhar)
                    # O 'unique_together' já cuida disso, mas é bom evitar queries desnecessárias.
                    if not ServicoUnidade.objects.filter(unidade=unidade, servico=servico).exists():
                        servicos_unidade_a_criar.append(
                            ServicoUnidade(
                                unidade=unidade,
                                servico=servico,
                                # status e progresso usarão os defaults definidos no modelo
                            )
                        )

            # 3. Cria todos os objetos de uma vez para otimizar o banco de dados
            ServicoUnidade.objects.bulk_create(servicos_unidade_a_criar)