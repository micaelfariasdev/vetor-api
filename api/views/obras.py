from rest_framework.viewsets import ModelViewSet
from ..serializer import ObrasSerializer
from engenharia.models import Obras


class ObrasApiViewSet(ModelViewSet):
    queryset = Obras.objects.all()
    serializer_class = ObrasSerializer
