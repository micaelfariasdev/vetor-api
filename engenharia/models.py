from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max
from datetime import timedelta, time
from django.core.exceptions import ValidationError


class Servicos(models.Model):
    titulo = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.titulo


class Obras(models.Model):
    TIPOS_OBRA = [
        ('PREDIO', 'Prédio'),
        ('CONDOMINIO', 'Condomínio de Casas'),
        ('LOTEAMENTO', 'Loteamento'),
    ]

    nome = models.CharField(max_length=150)
    endereço = models.CharField(max_length=250, blank=True, null=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    tipo_obra = models.CharField(
        max_length=20, choices=TIPOS_OBRA, default='PREDIO')
    servicos = models.ManyToManyField(
        Servicos, blank=True, related_name='obras')

    def __str__(self):
        return f'{self.nome}'


class Andar(models.Model):
    obra = models.ForeignKey(
        Obras, on_delete=models.CASCADE, related_name='andares')
    nome = models.CharField(max_length=50)

    def __str__(self):
        return f'Andar {self.nome} - {self.obra.nome}'

    class Meta:
        unique_together = ('obra', 'nome')


class Unidade(models.Model):
    obra = models.ForeignKey(
        Obras, on_delete=models.CASCADE, related_name='unidades')
    andar = models.ForeignKey(
        Andar, on_delete=models.CASCADE, related_name='unidades', blank=True, null=True)
    nome_ou_numero = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.nome_ou_numero} - {self.obra.nome}'

    class Meta:
        unique_together = ('obra', 'andar', 'nome_ou_numero')


class ServicoUnidade(models.Model):
    STATUS_CHOICES = [
        ('NAO_INICIADO', 'Não Iniciado'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDO', 'Concluído'),
    ]

    unidade = models.ForeignKey(
        Unidade, on_delete=models.CASCADE, related_name='servicos_unidade')
    servico = models.ForeignKey(Servicos, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='NAO_INICIADO')
    progresso = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        unique_together = ('unidade', 'servico')

    def save(self, *args, **kwargs):
        if self.progresso == 100.00:
            self.status = 'CONCLUIDO'
        elif self.progresso == 0.00:
            self.status = 'NAO_INICIADO'
        elif self.progresso > 0.00 and self.progresso < 100.00:
            self.status = 'EM_ANDAMENTO'

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.servico.titulo} - Obra {self.unidade.andar.obra.nome} andar {self.unidade.andar.nome} unidade {self.unidade.nome_ou_numero} ({self.status})'


class Colaborador(models.Model):
    nome = models.CharField(max_length=150)
    obra = models.ForeignKey(Obras, blank=True, null=-True,
                             related_name='colaboradores', on_delete=models.CASCADE)
    cargo = models.CharField(max_length=100)
    situacao = models.CharField(choices=[(
        'ASSINADO', 'Assinado'), ('FREE', 'Freelancer')], max_length=20, default='ASSINADO')

    def __str__(self):
        return f'{self.nome} - {self.cargo}'


class MesPonto(models.Model):
    mes = models.IntegerField(choices=[(i, i)
                                       for i in range(1, 13)], default=1)
    ano = models.IntegerField()
    obra = models.ForeignKey(Obras, blank=True, null=-True,
                             related_name='ponto_mes', on_delete=models.CASCADE)


class Ponto(models.Model):
    colaborador = models.ForeignKey(
        Colaborador, on_delete=models.CASCADE, related_name='pontos')
    data = models.DateField()
    entrada_manha = models.TimeField(null=True, blank=True)
    entrada_tarde = models.TimeField(null=True, blank=True)
    saida_manha = models.TimeField(null=True, blank=True)
    saida_tarde = models.TimeField(null=True, blank=True)
    horas_trabalhadas = models.CharField(max_length=150, null=True, blank=True)
    feriado = models.BooleanField(default=False, verbose_name='Feriado?')
    atestado = models.BooleanField(default=False, verbose_name='Atestado?')
    falta = models.BooleanField(default=False, verbose_name='Falta?')
    ferias = models.BooleanField(default=False, verbose_name='Ferias?')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['colaborador', 'data'], name='unique_ponto_colaborador_dia')
        ]

    def clean(self):
        if Ponto.objects.filter(colaborador=self.colaborador, data=self.data).exclude(pk=self.pk).exists():
            raise ValidationError(
                "Este colaborador já possui ponto registrado neste dia.")

    def save(self, *args, **kwargs):
        total_horas = timedelta()  # acumula como timedelta

        if self.entrada_manha and self.saida_manha:
            delta_manha = timedelta(
                hours=self.saida_manha.hour, minutes=self.saida_manha.minute
            ) - timedelta(
                hours=self.entrada_manha.hour, minutes=self.entrada_manha.minute
            )
            total_horas += delta_manha

        if self.entrada_tarde and self.saida_tarde:
            delta_tarde = timedelta(
                hours=self.saida_tarde.hour, minutes=self.saida_tarde.minute
            ) - timedelta(
                hours=self.entrada_tarde.hour, minutes=self.entrada_tarde.minute
            )
            total_horas += delta_tarde

        # Converte timedelta em horas e minutos
        total_segundos = int(total_horas.total_seconds())
        h = total_segundos // 3600
        m = (total_segundos % 3600) // 60

        # Guarda como datetime.time
        self.horas_trabalhadas = f"{h:02d}:{m:02d}"

        if self.atestado or self.falta:
            self.horas_trabalhadas = '00:00'
            self.entrada_manha = '00:00'
            self.saida_manha = '00:00'
            self.entrada_tarde = '00:00'
            self.saida_tarde = '00:00'

        super().save(*args, **kwargs)


class DespesasMes(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    obra = models.ForeignKey(Obras, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    mes = models.IntegerField(choices=[(i, i)
                              for i in range(1, 13)], default=1)
    ano = models.IntegerField()

    def __str__(self):
        return f"Despesas de {self.mes}/{self.ano} - {self.author.username}"


class DespesasItem(models.Model):
    despesas_mes = models.ForeignKey(
        DespesasMes, on_delete=models.CASCADE, related_name='despesas')
    data = models.DateField()
    documento = models.CharField(max_length=50)
    titulo = models.CharField(max_length=50)
    empresa = models.CharField(max_length=150)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField(null=True, blank=True)


class Cronograma(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    obra = models.ForeignKey(Obras, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    final = models.DateField(blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cronograma {str(self.obra).upper()} - Modificado em {self.atualizado_em.strftime('%d/%m/%Y')}"


class ServicoCronograma(models.Model):
    uid = models.IntegerField(null=True, blank=True)
    cronograma = models.ForeignKey(
        Cronograma, on_delete=models.CASCADE, related_name='servicos')
    pai = models.ForeignKey('self', null=True, blank=True,
                            on_delete=models.CASCADE, related_name='subservicos')
    nivel = models.IntegerField(
        choices=[(i, i) for i in range(1, 5)], default=1)
    titulo = models.CharField(max_length=150)
    inicio = models.DateField()
    dias = models.IntegerField(null=True, blank=True)
    fim = models.DateField(blank=True)
    progresso = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0)
    codigo = models.CharField(max_length=50, blank=True, editable=False)

    # Dependência entre tarefas (tipo Project)
    predecessores = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='sucessores')

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"

    def gerar_codigo(self):
        if not self.pai:
            nivel_irmaos = ServicoCronograma.objects.filter(
                cronograma=self.cronograma, pai__isnull=True)
        else:
            nivel_irmaos = self.pai.subservicos.all()

        total = nivel_irmaos.count() + 1
        prefixo = self.pai.codigo + '.' if self.pai else ''
        sequencia = f"{total:03d}" if self.pai else f"{total:02d}"
        return prefixo + sequencia

    # def ajustar_datas_por_dependencia(self, propagacao=True, atualizados=None):
    #     if atualizados is None:
    #         atualizados = set()

    #     if self.pk in atualizados:
    #         return  # evita reprocessar mesmo objeto

    #     maior_fim = self.predecessores.aggregate(Max('fim'))['fim__max']

    #     if maior_fim:
    #         duracao = (self.fim - self.inicio).days
    #         nova_inicio = maior_fim + timedelta(days=1)
    #         nova_fim = nova_inicio + timedelta(days=duracao)

    #         if self.inicio != nova_inicio or self.fim != nova_fim:
    #             self.inicio = nova_inicio
    #             self.fim = nova_fim
    #             super().save(update_fields=['inicio', 'fim'])
    #             atualizados.add(self.pk)

    #     if propagacao:
    #         for sucessor in self.sucessores.all():
    #             sucessor.ajustar_datas_por_dependencia(propagacao=True, atualizados=atualizados)

    def ajustar_final(self):
        self.fim = self.inicio + timedelta(days=self.dias)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.gerar_codigo()

        if self.inicio and self.dias is not None:
            self.fim = self.inicio + timedelta(days=self.dias)

        super().save(*args, **kwargs)


class Medicao(models.Model):
    data_medicao = models.DateField(auto_now_add=True)
    data_pagamento = models.DateField(blank=True, null=True)
    obra = models.ForeignKey(
        Obras,
        on_delete=models.CASCADE,
        related_name='medicoes'
    )

    def __str__(self):
        return f"Medição em {self.data_medicao} para a obra {self.obra.nome}"

    class Meta:
        verbose_name = "Medição"
        verbose_name_plural = "Medições"


class MedicaoColaborador(models.Model):
    medicao = models.ForeignKey(
        Medicao,
        on_delete=models.CASCADE,
        related_name='colaboradores_associados'
    )
    colaborador = models.ForeignKey(
        Colaborador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicoes_associadas'
    )

    def __str__(self):

        return f"{self.colaborador.nome} em Medição {self.medicao.id}"

    class Meta:
        unique_together = ('medicao', 'colaborador')
        verbose_name = "Colaborador em Medição"
        verbose_name_plural = "Colaboradores em Medições"


class ItemMedicao(models.Model):
    colaborador = models.ForeignKey(
        MedicaoColaborador,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    servico_unidade = models.ForeignKey(
        ServicoUnidade,
        on_delete=models.CASCADE,
        related_name='itens_medicao'
    )
    quantidade_feita = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )

    def save(self, *args, **kwargs):
        self.valor_total = self.quantidade_feita * self.valor_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantidade_feita} de {self.servico_unidade.servico.titulo} para {self.colaborador.nome}"

    class Meta:
        verbose_name = "Item de Medição"
        verbose_name_plural = "Itens de Medição"
