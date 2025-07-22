from .models import Cronograma, ServicoCronograma
from django.contrib import admin
from . import models


@admin.register(models.Obras)
class ObrasAdimin(admin.ModelAdmin):
    list_display = ['nome',  'endereço']


@admin.register(models.DespesasMes)
class DespesasMesAdimin(admin.ModelAdmin):
    list_display = ['author', 'obra', 'criado_em',
                    'atualizado_em', 'mes', 'ano',]


class ServicoCronogramaInline(admin.TabularInline):
    model = ServicoCronograma
    extra = 0
    fields = ['titulo','dias', 'inicio', 'fim', 'progresso']
    show_change_link = True


@admin.register(Cronograma)
class CronogramaAdmin(admin.ModelAdmin):
    list_display = ['id', 'obra', 'author', 'criado_em', 'atualizado_em']
    list_filter = ['obra', 'author']
    search_fields = ['obra__nome', 'author__username']
    inlines = [ServicoCronogramaInline]


@admin.register(ServicoCronograma)
class ServicoCronogramaAdmin(admin.ModelAdmin):
    list_editable = ['dias']
    list_display = ['uid','titulo','dias','inicio', 'fim', 'progresso']
    list_filter = ['nivel', 'cronograma__obra']
    search_fields = ['titulo', 'cronograma__obra__nome']
    autocomplete_fields = ['pai', 'cronograma']
    readonly_fields = ['uid', 'codigo']
