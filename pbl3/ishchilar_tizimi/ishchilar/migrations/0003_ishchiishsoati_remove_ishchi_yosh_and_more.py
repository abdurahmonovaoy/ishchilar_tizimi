# Generated by Django 5.1.3 on 2024-12-05 04:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ishchilar', '0002_lavozim_alter_ishchi_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='IshchiIshSoati',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('boshlanish_vaqti', models.TimeField()),
                ('tugash_vaqti', models.TimeField()),
            ],
        ),
        migrations.RemoveField(
            model_name='ishchi',
            name='yosh',
        ),
        migrations.AddField(
            model_name='ishchi',
            name='tugilgan_sana',
            field=models.DateField(default=datetime.date(2000, 1, 1), verbose_name='Tug‘ilgan sana'),
        ),
        migrations.AlterField(
            model_name='ishchi',
            name='familiya',
            field=models.CharField(max_length=100, verbose_name='Familiya'),
        ),
        migrations.AlterField(
            model_name='ishchi',
            name='ishga_kirgan_sana',
            field=models.DateField(default=datetime.date.today, verbose_name='Ishga kirgan sana'),
        ),
        migrations.AlterField(
            model_name='ishchi',
            name='ism',
            field=models.CharField(max_length=100, verbose_name='Ism'),
        ),
    ]
