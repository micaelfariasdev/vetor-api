from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver
from django.shortcuts import render
from rest_framework.views import APIView
import re


def get_all_urls(urlpatterns, prefix=''):
    """
    Função auxiliar para coletar todas as URLs do projeto.
    """
    url_list = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            url_list.extend(get_all_urls(pattern.url_patterns,
                            prefix=prefix + str(pattern.pattern)))
        elif isinstance(pattern, URLPattern):
            if hasattr(pattern, 'callback') and pattern.callback is not None:
                view_name = pattern.callback.__name__
                url_name = pattern.name if hasattr(
                    pattern, 'name') and pattern.name else "N/A"

                methods = []
                try:
                    view_class = pattern.callback.__self__.__class__
                    if issubclass(view_class, APIView):
                        methods = [method.upper() for method in view_class.http_method_names if hasattr(
                            view_class, method) and method not in ['options', 'head']]
                except (AttributeError, TypeError):
                    if hasattr(pattern.callback, 'view_class') and hasattr(pattern.callback.view_class, 'http_method_names'):
                        methods = [method.upper() for method in pattern.callback.view_class.http_method_names if hasattr(
                            pattern.callback.view_class, method) and method not in ['options', 'head']]
                    else:
                        methods = ['GET', 'POST']

                readable_url = str(pattern.pattern)
                readable_url = readable_url.replace('^', '').replace('$', '')

                readable_url = re.sub(
                    r'\(\?P<([^>]+)>[^)]+\)', r'<\1>', readable_url)

                readable_url = re.sub(
                    r'\\.\(\?P<format>[^)]+\)', r'.<format>', readable_url)

                url_list.append({
                    'url': prefix + readable_url,
                    'nome': url_name,
                    'view': view_name,
                    'methods': methods
                })
    return url_list


def listar_urls_api(request):
    """
    Renderiza o painel de URLs da API, agrupando-as.
    """
    resolver = get_resolver()
    urls_do_projeto = get_all_urls(resolver.url_patterns)

    urls_filtradas = [
        url for url in urls_do_projeto if '.<format>' not in url['url']]

    agrupado = {}
    for url in urls_filtradas:
        if url['url'].split('/')[0] in 'admin media static':
            continue
        if url['nome'] in 'api-root':
            continue

        caminho_url = url['url'].strip('/').split('/')

        grupo_principal = caminho_url[0] if len(caminho_url) > 0 else 'raiz'
        subgrupo = caminho_url[1] if len(caminho_url) > 1 else 'geral'

        if grupo_principal not in agrupado:
            agrupado[grupo_principal] = {}

        if subgrupo not in agrupado[grupo_principal]:
            agrupado[grupo_principal][subgrupo] = []

        agrupado[grupo_principal][subgrupo].append(url)

    context = {
        'agrupado': agrupado
    }

    return render(request, 'engenharia/urls_panel.html', context)
