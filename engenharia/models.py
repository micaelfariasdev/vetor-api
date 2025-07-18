from django.db import models
from django.contrib.auth.models import User


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
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cronograma {str(self.obra).upper()} - Modificado em {self.atualizado_em.strftime('%d/%m/%Y')}"


class ServicoCronograma(models.Model):
    cronograma = models.ForeignKey(
        Cronograma, on_delete=models.CASCADE, related_name='servicos')
    pai = models.ForeignKey('self', null=True, blank=True,
                            on_delete=models.CASCADE, related_name='subservicos')
    nivel = models.IntegerField(
        choices=[(i, i) for i in range(1, 5)], default=1)
    titulo = models.CharField(max_length=150)
    inicio = models.DateField()
    fim = models.DateField()
    progresso = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0)
    codigo = models.CharField(max_length=50, blank=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.gerar_codigo()
        super().save(*args, **kwargs)

    def gerar_codigo(self):
        if not self.pai:
            prefixo = ''
            nivel_irmaos = ServicoCronograma.objects.filter(
                cronograma=self.cronograma, pai__isnull=True)
        else:
            prefixo = self.pai.codigo + '.'
            nivel_irmaos = self.pai.subservicos.all()

        total = nivel_irmaos.count() + 1
        sequencia = f"{total:03d}"
        if not self.pai:
            return f"{total:02d}"  # para nível 1: 01, 02, ...
        return prefixo + sequencia

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"
