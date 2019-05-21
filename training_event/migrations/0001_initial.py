# Generated by Django 2.2 on 2019-05-21 03:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('training_program', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampusEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='最近修改时间')),
                ('name', models.CharField(max_length=64, verbose_name='活动名称')),
                ('time', models.DateTimeField(verbose_name='活动时间')),
                ('location', models.CharField(max_length=64, verbose_name='活动地点')),
                ('num_hours', models.FloatField(verbose_name='活动学时')),
                ('num_participants', models.PositiveIntegerField(verbose_name='活动人数')),
                ('deadline', models.DateTimeField(verbose_name='截止报名时间')),
                ('num_enrolled', models.PositiveSmallIntegerField(default=0, verbose_name='报名人数')),
                ('description', models.TextField(default='', verbose_name='活动描述')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='training_program.Program', verbose_name='培训项目')),
            ],
            options={
                'verbose_name': '校内培训活动',
                'verbose_name_plural': '校内培训活动',
                'permissions': (('add_campusevent', '允许添加校内培训活动'), ('view_campusevent', '允许查看校内培训活动'), ('change_campusevent', '允许修改校内培训活动'), ('delete_campusevent', '允许删除校内培训活动')),
                'abstract': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='OffCampusEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='最近修改时间')),
                ('name', models.CharField(max_length=64, verbose_name='活动名称')),
                ('time', models.DateTimeField(verbose_name='活动时间')),
                ('location', models.CharField(max_length=64, verbose_name='活动地点')),
                ('num_hours', models.FloatField(verbose_name='活动学时')),
                ('num_participants', models.PositiveIntegerField(verbose_name='活动人数')),
            ],
            options={
                'verbose_name': '校外培训活动',
                'verbose_name_plural': '校外培训活动',
                'abstract': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='EventCoefficient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.PositiveSmallIntegerField(choices=[(0, '参与'), (1, '专家')], default=0, verbose_name='参与角色')),
                ('coefficient', models.FloatField(default=0.0, verbose_name='角色系数')),
                ('hours_option', models.PositiveSmallIntegerField(choices=[(0, '正常计算'), (1, '向上取整'), (2, '向下取整'), (3, '四舍五入')], default=0, verbose_name='学时取整方式')),
                ('workload_option', models.PositiveSmallIntegerField(choices=[(0, '正常计算'), (1, '向上取整'), (2, '向下取整'), (3, '四舍五入')], default=0, verbose_name='工作量取整方式')),
                ('campus_event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='training_event.CampusEvent', verbose_name='校内培训活动')),
                ('off_campus_event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='training_event.OffCampusEvent', verbose_name='校外培训活动')),
            ],
            options={
                'verbose_name': '培训活动系数',
                'verbose_name_plural': '培训活动系数',
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('enroll_method', models.PositiveSmallIntegerField(choices=[(0, '网页报名'), (1, '移动端报名'), (2, '二维码报名'), (3, '邮件报名'), (4, '管理员导入')], default=0, verbose_name='报名渠道')),
                ('campus_event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training_event.CampusEvent', verbose_name='校内活动')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '活动报名记录',
                'verbose_name_plural': '活动报名记录',
                'permissions': (('add_enrollment', '允许添加活动报名记录'), ('delete_enrollment', '允许删除活动报名记录')),
                'default_permissions': (),
                'unique_together': {('campus_event', 'user')},
            },
        ),
    ]
