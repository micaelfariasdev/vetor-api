from rest_framework.viewsets import ModelViewSet
from .serializer import DespesasMesSerializer, DespesasItemSerializer
from engenharia.models import DespesasMes, DespesasItem
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

# Create your views here.


class DespesasMesApiViewSet(ModelViewSet):
    queryset = DespesasMes.objects.all()
    serializer_class = DespesasMesSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not request.data.get('author'):
            data['author'] = request.user.id
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)


class DespesasItemApiViewSet(ModelViewSet):
    queryset = DespesasItem.objects.all()
    serializer_class = DespesasItemSerializer

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)


class ExcelToItensDespesas(APIView):
    serializer_class = DespesasItemSerializer
    

    def post(self, request, *args, **kwargs):
        despesas_mes = request.POST.get('Object')
        despesas_clear = DespesasItem.objects.filter(despesas_mes=despesas_mes).all()
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "Porfavor, envie o arquivo correto"}, status=status.HTTP_400_BAD_REQUEST)
        for despesas in despesas_clear:
            despesas.delete()

        import pandas as pd
        import numpy as np

        df = pd.read_excel(file, sheet_name=0, header=None)
        df.columns = df.iloc[1]
        df = df[2:]
        df = df.drop(columns=[col for col in df.columns if pd.isna(col)])
        df.drop(['Obra', 'Unidade construtiva', 'Célula construtiva', 'Etapa',
                'Subetapa', 'Serviço', 'Data da baixa', 'Or', 'Valor'], axis=1, inplace=True)
        df["Valor do documento"] = pd.to_numeric(
            df["Valor do documento"], errors="coerce").round(2)
        df.sort_values('Credor/Histórico', inplace=True)
        df.drop_duplicates(subset='Título/Parcela', inplace=True)
        df = df.replace({np.nan: ' '})
        df = df.rename(columns={
            'Data': 'data',
            'Documento': 'documento',
            'Título/Parcela': 'titulo',
            'Credor/Histórico': 'empresa',
            'Valor do documento': 'valor',
            'Observação': 'descricao'
        })
        df['data'] = pd.to_datetime(df['data'], dayfirst=True).dt.date
        try:
            for _, row in df.iterrows():
                data = row.to_dict()
                data['despesas_mes'] = despesas_mes

                serializer = self.serializer_class(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    print(serializer.errors)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Arquivo processado com sucesso"}, status=status.HTTP_200_OK)