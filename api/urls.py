from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter



router = DefaultRouter()
router.register('despesas', views.DespesasMesApiViewSet, basename='despesas')
router.register('despesasitens', views.DespesasItemApiViewSet, basename='despesas-itens')
urlpatterns = router.urls

urlpatterns += [
    path('excel/', views.ExcelToItensDespesas.as_view(), name='excel-to-itens-despesas'),
]