# Generated by Django 2.2 on 2019-06-12 11:51

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('training_event', '0005_auto_20190527_1403'),
        ('training_record', '0002_auto_20190526_1904'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='record',
            unique_together={('user', 'campus_event')},
        ),
    ]
