# Generated by Django 5.1.4 on 2025-03-13 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hodimlar', '0004_alter_hodim_options_alter_hodim_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hodim',
            name='lavozim',
            field=models.CharField(choices=[('Tikuvch', 'Tikuvchi'), ('Orta kesuv', 'Orta kesuv'), ('Kesuv', 'Kesuv'), ('Mehanik', 'Mehanik'), ('Ish bay', 'Ish bay')], default='Tikuvchi', max_length=50),
        ),
    ]
