# Generated by Django 2.2 on 2019-06-12 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tmsftt_auth', '0006_auto_20190606_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='name',
            field=models.CharField(max_length=50, verbose_name='院系'),
        ),
    ]
