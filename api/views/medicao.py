from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from engenharia import models as MOD
from .. import serializer as SER
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response


class MedicaoApiViewSet(ModelViewSet):
    queryset = MOD.Medicao.objects.all()
    serializer_class = SER.MedicaoSerializer
    # permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]




class ItemMedicaoApiViewSet(ModelViewSet):
    queryset = MOD.ItemMedicao.objects.all()
    serializer_class = SER.ItemMedicaoSerializer
    # permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class MedicaoColaboradorApiViewSet(ModelViewSet):
    queryset = MOD.MedicaoColaborador.objects.all()
    serializer_class = SER.MedicaoColaboradorSerializer
    # permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
