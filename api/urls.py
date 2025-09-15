from . import views
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
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
router.register('mes-ponto', views.MesPontoApiViewSet,
                basename='mes-ponto')
router.register('unidade', views.UnidadeApiViewSet,
                basename='unidade')
router.register('servico', views.ServicosApiViewSet,
                basename='servico')
router.register('servico-unidade', views.ServicosUnidadeApiViewSet,
                basename='servico-unidade')
router.register('andar', views.AndarApiViewSet,
                basename='andar')
router.register('medicao', views.MedicaoApiViewSet,
                basename='medicao')
router.register('medicao-colaborador', views.MedicaoColaboradorApiViewSet,
                basename='medicao-colaborador')
router.register('item-medicao', views.ItemMedicaoApiViewSet,
                basename='item-medicao')

urlpatterns = router.urls

urlpatterns += [
    path('excel/', views.ExcelToItensDespesas.as_view(),
         name='excel-to-itens-despesas'),
    path('xmlcronograma/', views.XMLToCronograma.as_view(), name='xml-cronograma'),
    path('cronograma/recalcular/<int:cronograma_id>/',
         views.recalcular_cronograma),
    path('ponto/pdf/<int:mes_id>/',
         views.pdf_pontos_relatorio),
    path('ponto/pdf/<int:mes_id>/<int:col>/',
         views.pdf_pontos_relatorio),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("token/", views.CookieTokenObtainPairView.as_view(),
         name="token_obtain_pair"),
    path("token/refresh/", views.CookieTokenRefreshView.as_view(),
         name="token_refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("infos/", views.InfoView.as_view(), name="info"),
    path("pontos/<int:ano>/<int:mes>/zip",
         views.proxy_download_zip, name="pdf"),
]
