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
    mes = models.IntegerField(choices=[(i, i) for i in range(1, 13)], default=1)
    ano = models.IntegerField()

    def __str__(self):
        return f"Despesas de {self.mes}/{self.ano} - {self.author.username}"

class DespesasItem(models.Model):
    despesas_mes = models.ForeignKey(DespesasMes, on_delete=models.CASCADE, related_name='despesas')
    data = models.DateField()
    documento = models.CharField(max_length=50)
    titulo = models.CharField(max_length=50)
    empresa = models.CharField(max_length=150)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField(null=True, blank=True)

