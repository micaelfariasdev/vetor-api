from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max
from datetime import timedelta


class Obras(models.Model):
    nome = models.CharField(max_length=150)
    endereço = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return f'{self.nome}'


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

    def ajustar_datas_por_dependencia(self, propagacao=True):
        maior_fim = self.predecessores.aggregate(Max('fim'))['fim__max']

        if maior_fim:
            duracao = (self.fim - self.inicio).days
            nova_inicio = maior_fim + timedelta(days=1)
            nova_fim = nova_inicio + timedelta(days=duracao)

            if self.inicio != nova_inicio or self.fim != nova_fim:
                self.inicio = nova_inicio
                self.fim = nova_fim
                self.save()  # agora salva antes de propagar

        if propagacao:
            for sucessor in self.sucessores.all():
                sucessor.ajustar_datas_por_dependencia()

    def ajustar_final(self):
        self.fim = self.inicio + timedelta(days=self.dias)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.gerar_codigo()

        # Cálculo de fim antes de salvar
        if self.inicio and self.dias is not None:
            self.fim = self.inicio + timedelta(days=self.dias)

        super().save(*args, **kwargs)

        # Ajusta dependências depois de salvar
        self.ajustar_datas_por_dependencia()
