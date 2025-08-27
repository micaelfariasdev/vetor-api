from rest_framework import serializers
from engenharia.models import *
from django.contrib.auth.models import User


class DespesasMesSerializer(serializers.ModelSerializer):
    itens = serializers.SerializerMethodField()
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=True)
    username = serializers.CharField(source='author.username', read_only=True)
    obra_name = serializers.CharField(source='obra.nome', read_only=True)

    class Meta:
        model = DespesasMes
        fields = ['id', 'obra', 'obra_name', 'author', 'username', 'criado_em',
                  'atualizado_em', 'mes', 'ano', 'itens']

    def get_itens(self, obj):
        itens = DespesasItem.objects.filter(despesas_mes=obj)
        return DespesasItemSerializer(itens, many=True).data


class DespesasItemSerializer(serializers.ModelSerializer):
    despesas_mes = serializers.PrimaryKeyRelatedField(
        queryset=DespesasMes.objects.all())

    class Meta:
        model = DespesasItem
        fields = ['id', 'despesas_mes', 'data', 'documento',
                  'titulo', 'empresa', 'valor', 'descricao']


class ObrasSerializer(serializers.ModelSerializer):

    class Meta:
        model = Obras
        fields = ['id', 'nome', 'endereço']


class CronogramaSerializer(serializers.ModelSerializer):
    obra_name = serializers.CharField(source='obra.nome', read_only=True)

    class Meta:
        model = Cronograma
        fields = '__all__'


class ServicoCronogramaSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServicoCronograma
        fields = '__all__'


class ColaboradorSerializer(serializers.ModelSerializer):
    obra_name = serializers.CharField(source='obra.nome', read_only=True)

    class Meta:
        model = Colaborador
        fields = '__all__'


class PontoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ponto
        fields = '__all__'


class MesPontoSerializer(serializers.ModelSerializer):

    class Meta:
        model = MesPonto
        fields = '__all__'
