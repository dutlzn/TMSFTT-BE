# Generated by Django 2.2 on 2019-05-15 11:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('training_event', '0003_remove_enrollment_is_participated'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventcoefficient',
            options={'default_permissions': (), 'verbose_name': '培训活动系数', 'verbose_name_plural': '培训活动系数'},
        ),
        migrations.AlterModelOptions(
            name='offcampusevent',
            options={'default_permissions': (), 'verbose_name': '校外培训活动', 'verbose_name_plural': '校外培训活动'},
        ),
    ]