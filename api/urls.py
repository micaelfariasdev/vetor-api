from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('despesas', views.DespesasMesApiViewSet, basename='despesas')
router.register('despesasitens', views.DespesasItemApiViewSet,
                basename='despesas-itens')
router.register('obras', views.ObrasApiViewSet, basename='obras')
router.register('cronograma', views.CronogramasApiViewSet,
                basename='cronograma')
router.register('servicos-cronograma', views.ServicosCronogramasApiViewSet,
                basename='servicos-cronograma')
router.register('colaboradores', views.ColaboradorApiViewSet,
                basename='colaboradores')
router.register('ponto', views.PontoApiViewSet,
                basename='ponto')
urlpatterns = router.urls

urlpatterns += [
    path('excel/', views.ExcelToItensDespesas.as_view(),
         name='excel-to-itens-despesas'),
    path('xmlcronograma/', views.XMLToCronograma.as_view(), name='xml-cronograma'),
    path('cronograma/recalcular/<int:cronograma_id>/',
         views.recalcular_cronograma),
]
