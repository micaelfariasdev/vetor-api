# Generated by Django 5.2.1 on 2025-07-22 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engenharia', '0011_servicocronograma_dias'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicocronograma',
            name='uid',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
