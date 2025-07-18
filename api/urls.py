from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter



router = DefaultRouter()
router.register('despesas', views.DespesasMesApiViewSet, basename='despesas')
router.register('despesasitens', views.DespesasItemApiViewSet, basename='despesas-itens')
router.register('obras', views.ObrasApiViewSet, basename='obras')
urlpatterns = router.urls

urlpatterns += [
    path('excel/', views.ExcelToItensDespesas.as_view(), name='excel-to-itens-despesas'),
    path('xmlcronograma/', views.XMLToCronograma.as_view(), name='xml-cronograma'),
]
