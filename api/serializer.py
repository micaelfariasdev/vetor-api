from datetime import datetime
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


class ServicosSerializer(serializers.ModelSerializer):

    class Meta:
        model = Servicos
        fields = '__all__'


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
    colaborador_name = serializers.CharField(
        source='colaborador.nome', read_only=True)

    class Meta:
        model = Ponto
        fields = '__all__'


class MesPontoSerializer(serializers.ModelSerializer):
    obra_name = serializers.CharField(source='obra.nome', read_only=True)

    class Meta:
        model = MesPonto
        fields = '__all__'


class UnidadeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Unidade
        fields = '__all__'


class ServicosUnidadeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServicoUnidade
        fields = '__all__'


class AndarSerializer(serializers.ModelSerializer):
    unidades = UnidadeSerializer(many=True, read_only=True)

    class Meta:
        model = Andar
        fields = '__all__'


class ObrasSerializer(serializers.ModelSerializer):
    servicos = ServicosSerializer(many=True, read_only=True)
    unidades = serializers.SerializerMethodField()
    andares = serializers.SerializerMethodField()

    class Meta:
        model = Obras
        fields = "__all__"

    def get_unidades(self, obj):
        if obj.tipo_obra != 'PREDIO':
            return UnidadeSerializer(obj.unidades.all(), many=True).data
        return []

    def get_andares(self, obj):
        if obj.tipo_obra == 'PREDIO':
            return AndarSerializer(obj.andares.all(), many=True).data
        return []


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email",
                  "password", 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"]
        )
        return user


class ItemMedicaoSerializer(serializers.ModelSerializer):
    servico = serializers.CharField(
        source='servico_unidade.servico.titulo', read_only=True)
    andar = serializers.CharField(
        source='servico_unidade.unidade.andar.nome', read_only=True)
    unidade = serializers.CharField(
        source='servico_unidade.unidade.nome_ou_numero', read_only=True)

    class Meta:
        model = ItemMedicao
        fields = ['id', 'colaborador', 'servico_unidade', 'servico', 'andar', 'unidade', 'quantidade_feita',
                  'valor_unitario', 'valor_total']
        read_only_fields = ['valor_total']


class MedicaoColaboradorSerializer(serializers.ModelSerializer):
    itens = ItemMedicaoSerializer(many=True, read_only=True)
    colaborador_name = serializers.CharField(
        source='colaborador.nome', read_only=True)
    valor_total = serializers.SerializerMethodField()

    class Meta:
        model = MedicaoColaborador
        fields = ['id', 'colaborador', 'colaborador_name',
                  'medicao', 'valor_total', 'itens']

    def get_valor_total(self, obj):
        total = 0
        for item in obj.itens.all():
            total += item.valor_total
        return total

# Serializer Principal para a Medição


class MedicaoSerializer(serializers.ModelSerializer):
    # Campos de relacionamento para aninhar a exibição de dados
    colaboradores = MedicaoColaboradorSerializer(
        many=True, read_only=True)
    str = serializers.SerializerMethodField()
    valor_total = serializers.SerializerMethodField()

    class Meta:
        model = Medicao
        fields = ['id', 'obra', 'str', 'data_medicao', 'data_pagamento',
                  'valor_total', 'colaboradores', ]

    def get_str(self, obj):
        if not obj.data_medicao or not obj.data_pagamento:
            return f'Medição da  Obra {obj.obra.nome}'
        data_med = obj.data_medicao
        data_pag = obj.data_pagamento

        resp = f'Medição {data_med.month:02}/{data_med.year} - Pagamento {data_pag.day:02}/{data_pag.month:02}/{data_pag.year} - Obra {obj.obra.nome}'
        return resp

    def get_valor_total(self, obj):
        total = 0
        for colaborador in obj.colaboradores.all():
            total += colaborador.valor_total
        return total
