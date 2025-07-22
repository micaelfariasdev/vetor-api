from django.contrib import admin
from . import models

@admin.register(models.Obras)
class ObrasAdimin(admin.ModelAdmin):
    list_display = ['nome',  'endereço'] 

@admin.register(models.DespesasMes)
class DespesasMesAdimin(admin.ModelAdmin):
    list_display = ['author','obra','criado_em','atualizado_em','mes','ano',] 
