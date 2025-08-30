import logging
from django.http import JsonResponse

# Obtenha uma instância do logger configurado em settings.py
# O nome 'api' corresponde ao novo logger que adicionamos
logger = logging.getLogger('api')

def api_endpoint(request):
    try:
        # Exemplo de log de informação
        logger.info("Acessando o endpoint da API.")
        
        # Sua lógica de negócios...
        dados = {'message': 'Bem-vindo à sua API!'}
        
        return JsonResponse(dados)
    
    except Exception as e:
        # Exemplo de log de erro
        logger.error(f"Ocorreu um erro na API: {e}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
