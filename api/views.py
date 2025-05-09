from rest_framework.viewsets import ModelViewSet 
from .serializer import DespesasMesSerializer, DespesasItemSerializer
from engenharia.models import DespesasMes, DespesasItem
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
class DespesasMesApiViewSet(ModelViewSet):
    queryset = DespesasMes.objects.all()
    serializer_class = DespesasMesSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED) 
        return super().create(request, *args, **kwargs)
    
class DespesasItemApiViewSet(ModelViewSet):
    queryset = DespesasItem.objects.all()
    serializer_class = DespesasItemSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED) 
        return super().create(request, *args, **kwargs)